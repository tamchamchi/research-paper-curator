import logging
from typing import Optional

from opensearchpy import OpenSearch, helpers

from src.config import Settings, get_settings
from src.services.embeddings.jina_client import JinaEmbeddingsClient
from src.services.opensearch.index_config_hybrid import SMALL_TALK_MAPPING

from .small_talk_data import SMALL_TALK_QA_PAIRS


class SmallTalkHandler:
    def __init__(
        self,
        embeddings_service: JinaEmbeddingsClient,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.opensearch_client = OpenSearch(
            hosts=[self.settings.opensearch.host],
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False,
        )
        self.embeddings_service = embeddings_service
        self.index_name = f"{self.settings.opensearch.index_name}-{self.settings.small_talk_handler.index_name}"
        self.cosine_similarity_threshold = (
            self.settings.small_talk_handler.cosine_similarity_threshold
        )

        logging.info("SmallTalkHandler initialized with small talk data")

    async def setup_small_talk_index(self):
        """Set up the OpenSearch index for small talk data and seed it with predefined question-answer pairs."""
        res_setup = None
        try:
            if not self.opensearch_client.indices.exists(index=self.index_name):
                logging.info(f"Creating small talk index: {self.index_name}")
                self.opensearch_client.indices.create(
                    index=self.index_name, body=SMALL_TALK_MAPPING
                )
                res_setup = await self._seed_small_talk_data()
                if res_setup:
                    logging.info(f"Small talk data indexed successfully: {res_setup}")
                else:
                    logging.error("Failed to index small talk data")
            else:
                logging.info(f"Small talk index already exists: {self.index_name}")

            return res_setup
        except Exception as e:
            logging.error(f"Error setting up small talk index: {e}")

    async def reindex_small_talk_data(self):
        """Reindex small talk data - useful if the predefined question-answer pairs are updated."""
        res_setup = None
        try:
            logging.info("Reindexing small talk data...")
            res_setup = await self._seed_small_talk_data()
            if res_setup:
                logging.info(f"Small talk data reindexed successfully: {res_setup}")
            else:
                logging.error("Failed to reindex small talk data")
            return res_setup
        except Exception as e:
            logging.error(f"Error reindexing small talk data: {e}")

    async def _seed_small_talk_data(self):
        """Seed the OpenSearch index with predefined small talk question-answer pairs."""
        small_talk_queries = list(SMALL_TALK_QA_PAIRS.keys())
        if not small_talk_queries:
            logging.warning("No small talk queries to index")
            return False

        logging.info(f"Seeding small talk data with {len(small_talk_queries)} entries")

        actions = []
        batch_size = 32
        for i in range(0, len(small_talk_queries), batch_size):
            batch_queries = small_talk_queries[i : i + batch_size]
            batch_embeddings = await self.embeddings_service.embed_passages(
                batch_queries, batch_size=batch_size
            )

            for j, query_text in enumerate(batch_queries):
                action = {
                    "_index": self.index_name,
                    "_id": f"small_talk_{i + j}",
                    "_source": {
                        "question_vector": batch_embeddings[j],
                        "original_query": query_text,
                        "small_talk_answer": SMALL_TALK_QA_PAIRS[query_text],
                    },
                }
                actions.append(action)

        success, failed = helpers.bulk(self.opensearch_client, actions, refresh=True)
        logging.info(f"Indexed {success} small talk entries, {failed} failed.")
        return True

    async def get_small_talk_response(self, query: str) -> Optional[str]:
        """Get a small talk response for the given query if it matches any predefined small talk questions."""
        try:
            query = query.lower().strip()
            query_embedding = await self.embeddings_service.embed_query(query)
            search_body = {
                "size": 1,
                "query": {
                    "knn": {
                        "question_vector": {
                            "vector": query_embedding,
                            "k": 1,
                        }
                    }
                },
            }
            response = self.opensearch_client.search(
                index=self.index_name, body=search_body
            )
            hits = response.get("hits", {}).get("hits", [])
            if hits:
                top_hit = hits[0]
                logging.info(f"Small talk search hit: {top_hit}")
                score = top_hit.get("_score", 0)
                if score >= self.cosine_similarity_threshold:
                    return top_hit["_source"]["small_talk_answer"]
            return None

        except Exception as e:
            logging.error(f"Error retrieving small talk response: {e}")
            return None
