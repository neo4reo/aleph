import logging
from elasticsearch.helpers import scan

from aleph.core import get_es, get_es_index
from aleph.index.mapping import TYPE_DOCUMENT, TYPE_RECORD  # noqa
from aleph.search.documents import documents_query, execute_documents_query  # noqa
from aleph.search.entities import entities_query, execute_entities_query  # noqa
from aleph.search.entities import suggest_entities, similar_entities  # noqa
from aleph.search.records import records_query, execute_records_query  # noqa

PAGE = 1000

log = logging.getLogger(__name__)


def scan_iter(query):
    """Scan the results of a query. No pagination is applied."""
    return scan(get_es(), query=query, index=get_es_index(),
                doc_type=[TYPE_DOCUMENT])
