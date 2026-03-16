import json
import logging
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.dependencies import (
    CacheDep,
    DomainClassifierDep,
    EmbeddingsDep,
    OllamaDep,
    OpenSearchDep,
    SmallTalkHandlerDep,
)
from src.schemas.api.ask import AskRequest, AskResponse

logger = logging.getLogger(__name__)

# Two separate routers - one for regular ask, one for streaming
ask_router = APIRouter(tags=["ask"])
stream_router = APIRouter(tags=["stream"])


async def _prepare_chunks_and_sources(
    request: AskRequest,
    opensearch_client,
    embeddings_service,
):
    """Shared function to prepare chunks and sources for RAG."""
    # Generate query embedding for hybrid search if enabled
    query_embedding = None
    search_mode = "bm25"

    if request.use_hybrid:
        try:
            query_embedding = await embeddings_service.embed_query(request.query)
            search_mode = "hybrid"
            logger.info("Generated query embedding for hybrid search")
        except Exception as e:
            logger.warning(f"Failed to generate embeddings, falling back to BM25: {e}")
            query_embedding = None
            search_mode = "bm25"

    # Retrieve top-k chunks
    logger.info(f"Retrieving top {request.top_k} chunks for query: '{request.query}'")

    # Execute one unified search call (BM25 only or hybrid BM25 + vector)
    # so both /ask and /stream share identical retrieval behavior.
    search_results = opensearch_client.search_unified(
        query=request.query,
        query_embedding=query_embedding,
        size=request.top_k,
        from_=0,
        categories=request.categories,
        use_hybrid=request.use_hybrid and query_embedding is not None,
        min_score=0.0,
    )

    # Extract chunks with minimal data for LLM
    chunks = []
    sources_set = set()  # Use set to automatically handle duplicates

    for hit in search_results.get("hits", []):
        arxiv_id = hit.get("arxiv_id", "")

        # Build minimal chunk for LLM (only content + arxiv_id)
        chunk_data = {
            "arxiv_id": arxiv_id,
            "chunk_text": hit.get("chunk_text", hit.get("abstract", "")),
        }
        chunks.append(chunk_data)

        # Build PDF URL from arxiv_id for sources (automatically deduplicates)
        if arxiv_id:
            arxiv_id_clean = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id_clean}.pdf"
            sources_set.add(pdf_url)

    # Convert set back to list for API schema compatibility.
    sources = list(sources_set)

    return chunks, sources, search_mode


@ask_router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    opensearch_client: OpenSearchDep,
    embeddings_service: EmbeddingsDep,
    ollama_client: OllamaDep,
    domain_classifier: DomainClassifierDep,
    small_talk_handler: SmallTalkHandlerDep,
    cache_client: CacheDep,
) -> AskResponse:
    """
    RAG endpoint for question answering.

    1. Retrieves top-k chunks using hybrid search
    2. Passes chunks to LLM with prompt template
    3. Returns structured answer with sources
    """
    try:
        start_time = time.perf_counter()

        # Check cache first
        cache_response = None
        if cache_client:
            try:
                cache_response = await cache_client.find_cached_response(request)
                if cache_response:
                    logger.info("Returning cached response for query")
                    return cache_response
            except Exception as e:
                logger.warning(f"Cache check failed, proceeding with normal flow: {e}")

        # Check service availability
        if not opensearch_client.health_check():
            raise HTTPException(
                status_code=503, detail="Search service is currently unavailable"
            )

        # Check Ollama service
        try:
            await ollama_client.health_check()
        except Exception as e:
            logger.error(f"Ollama service unavailable: {e}")
            raise HTTPException(
                status_code=503, detail="LLM service is currently unavailable"
            )

        # Guard against missing classifier dependency. In that case,
        # we default to in-domain and continue the RAG path.
        # This keeps the endpoint available even if classification is degraded.
        if not domain_classifier:
            logger.warning(
                "Domain classifier not available, proceeding without classification"
            )
            domain_label = 1  # Assume in-domain if classifier is not available
        else:
            domain_label = await domain_classifier.classify(request.query)
            logger.info(
                "Domain classification result for query '%s': %s",
                request.query,
                domain_label,
            )

        if domain_label == 0:
            # Out-of-domain queries are answered by the small-talk handler
            # (if available) and never sent to retrieval + LLM generation.
            logger.info(f"Query classified as out-of-domain: '{request.query}'")
            # Check if small talk handler is available
            if not small_talk_handler:
                logger.warning("Small talk handler is not available")
                small_talk_response = None
            else:
                small_talk_response = await small_talk_handler.get_small_talk_response(
                    request.query
                )
            logger.info(f"Small talk response: {small_talk_response}")

            if small_talk_response:
                response = AskResponse(
                    query=request.query,
                    answer=small_talk_response,
                    sources=[],
                    chunks_used=0,
                    search_mode="small_talk",
                )
            else:
                response = AskResponse(
                    query=request.query,
                    answer="Your question seems to be outside the scope of academic research papers. Please try asking about a research topic or paper.",
                    sources=[],
                    chunks_used=0,
                    search_mode="none",
                )

            # Store in cache before returning
            if cache_client:
                try:
                    await cache_client.store_response(request, response)
                except Exception as e:
                    logger.warning(f"Failed to store response in cache: {e}")
            return response

        # Run RAG flow for in-domain queries
        # Prepare chunks and sources using shared function
        chunks, sources, search_mode = await _prepare_chunks_and_sources(
            request, opensearch_client, embeddings_service
        )

        if not chunks:
            logger.warning(f"No chunks found for query: {request.query}")
            response = AskResponse(
                query=request.query,
                answer="I couldn't find any relevant information in the papers to answer your question.",
                sources=[],
                chunks_used=0,
                search_mode=search_mode,
            )
            # Store in cache before returning
            if cache_client:
                try:
                    await cache_client.store_response(request, response)
                except Exception as e:
                    logger.warning(f"Failed to store response in cache: {e}")
            return response

        logger.info(
            f"Retrieved {len(chunks)} chunks, generating answer with {request.model}"
        )

        # Generate answer using LLM
        # The model receives only the compact chunk payload (arxiv_id + chunk_text)
        # built in _prepare_chunks_and_sources.
        rag_response = await ollama_client.generate_rag_answer(
            query=request.query, chunks=chunks, model=request.model
        )

        logger.debug(f"RAG response: {rag_response}")

        # Prepare response using pre-built sources
        response = AskResponse(
            query=request.query,
            answer=rag_response.get("answer", "Unable to generate answer"),
            sources=sources,  # Use sources from search results
            chunks_used=len(chunks),
            search_mode=search_mode,
        )

        logger.info(f"Successfully generated answer for query: '{request.query}'")
        end_time = time.perf_counter()
        logger.info(f"Total processing time: {end_time - start_time:.2f} seconds")

        # Store in cache before returning
        if cache_client:
            try:
                await cache_client.store_response(request, response)
            except Exception as e:
                logger.warning(f"Failed to store response in cache: {e}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ask endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to process question: {str(e)}"
        )


@stream_router.post("/stream")
async def ask_question_stream(
    request: AskRequest,
    opensearch_client: OpenSearchDep,
    embeddings_service: EmbeddingsDep,
    ollama_client: OllamaDep,
    domain_classifier: DomainClassifierDep,
    small_talk_handler: SmallTalkHandlerDep,
    cache_client: CacheDep,
) -> StreamingResponse:
    """Streaming RAG endpoint - returns answer as it's generated."""

    async def generate_stream():
        try:
            # Check cache first
            if cache_client:
                try:
                    cached_response = await cache_client.find_cached_response(request)
                    if cached_response:
                        logger.info("Returning cached response for streaming query")
                        # Send metadata first (same format as non-cached)
                        metadata_response = {
                            "sources": cached_response.sources,
                            "chunks_used": cached_response.chunks_used,
                            "search_mode": cached_response.search_mode,
                        }
                        yield f"data: {json.dumps(metadata_response)}\n\n"

                        # Emulate token streaming for cached entries so the client
                        # can reuse the same rendering path for cached and live runs.
                        for chunk in cached_response.answer.split():
                            yield f"data: {json.dumps({'chunk': chunk + ' '})}\n\n"

                        # Send completion signal with just the final answer
                        yield f"data: {json.dumps({'answer': cached_response.answer, 'done': True})}\n\n"
                        return
                except Exception as e:
                    logger.warning(
                        f"Cache check failed, proceeding with normal flow: {e}"
                    )

            if not opensearch_client.health_check():
                yield f"data: {json.dumps({'error': 'Search service unavailable'})}\n\n"
                return

            await ollama_client.health_check()

            # Check if domain classifier is available
            if not domain_classifier:
                logger.warning(
                    "Domain classifier not available, proceeding without classification"
                )
                domain_label = 1
            else:
                domain_label = await domain_classifier.classify(request.query)
                logger.info(
                    "Domain classification result for streaming query '%s': %s",
                    request.query,
                    domain_label,
                )

            if domain_label == 0:
                logger.info(f"Query classified as out-of-domain: '{request.query}'")

                if small_talk_handler:
                    small_talk_response = (
                        await small_talk_handler.get_small_talk_response(request.query)
                    )
                    logger.info(f"Small talk response: {small_talk_response}")
                    if small_talk_response:
                        yield f"data: {json.dumps({'answer': small_talk_response, 'sources': [], 'done': True})}\n\n"
                        if cache_client:
                            try:
                                response_to_cache = AskResponse(
                                    query=request.query,
                                    answer=small_talk_response,
                                    sources=[],
                                    chunks_used=0,
                                    search_mode="small_talk",
                                )
                                await cache_client.store_response(
                                    request, response_to_cache
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to store small talk response in cache: {e}"
                                )
                        return
                else:
                    logger.warning("Small talk handler is not available")
                full_response = "Your question seems to be outside the scope of academic research papers. Please try asking about a research topic or paper."
                yield f"data: {json.dumps({'answer': full_response, 'sources': [], 'done': True})}\n\n"
                if cache_client:
                    try:
                        response_to_cache = AskResponse(
                            query=request.query,
                            answer=full_response,
                            sources=[],
                            chunks_used=0,
                            search_mode="none",
                        )
                        await cache_client.store_response(request, response_to_cache)
                    except Exception as e:
                        logger.warning(
                            f"Failed to store out-of-domain response in cache: {e}"
                        )
                return

            # Get chunks and sources using shared function
            chunks, sources, search_mode = await _prepare_chunks_and_sources(
                request, opensearch_client, embeddings_service
            )

            if not chunks:
                yield f"data: {json.dumps({'answer': 'No relevant information found.', 'sources': [], 'done': True})}\n\n"
                return

            # Send metadata first
            # Metadata is emitted before text chunks so clients can render sources
            # and retrieval diagnostics immediately.
            yield f"data: {json.dumps({'sources': sources, 'chunks_used': len(chunks), 'search_mode': search_mode})}\n\n"

            # Stream the answer
            full_response = ""
            async for chunk in ollama_client.generate_rag_answer_stream(
                query=request.query, chunks=chunks, model=request.model
            ):
                if chunk.get("response"):
                    text_chunk = chunk["response"]
                    full_response += text_chunk
                    yield f"data: {json.dumps({'chunk': text_chunk})}\n\n"

                if chunk.get("done", False):
                    yield f"data: {json.dumps({'answer': full_response, 'done': True})}\n\n"
                    break

            if cache_client:
                try:
                    response_to_cache = AskResponse(
                        query=request.query,
                        answer=full_response,
                        sources=sources,
                        chunks_used=len(chunks),
                        search_mode=search_mode,
                    )
                    await cache_client.store_response(request, response_to_cache)
                except Exception as e:
                    logger.warning(f"Failed to store response in cache: {e}")

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        # Keep plain text for backward compatibility with existing clients
        # that parse "data: ...\n\n" manually.
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
