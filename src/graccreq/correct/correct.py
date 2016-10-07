import logging
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan
from elasticsearch.exceptions import ElasticsearchException

logger = logging.getLogger(__name__)

class Corrections:
    """
    Generic class for correcting fields based on lookup to Elasticseearch table.

    The corrections are fetched and cached when the class is instantiated. Call
    fetch_corrections() to refresh the cache.
    """
    def __init__(self, uri, index, doc_type, match_fields, source_field, dest_field):
        """
        :param str uri: base URI to Elasticsearch REST API
        :param str index: Elasticsearch index to fetch corrections from.
        :param str doc_type: Elasticsearch document type to fetch corrections from.
        :param list match_fields: list of fields that are used to look up the corrections.
            The field names must be the same in the document and in the lookup index.
        :param str source_field: Field name in the lookup index containing the corrected name.
        :param str dest_field: Field name in the document .
        """
        self.es_uri = uri
        self.es_index = index
        self.es_doc_type = doc_type
        self.match_fields = match_fields
        self.source_field = source_field
        self.dest_field = dest_field

        self.fetch_corrections()

    def fetch_corrections(self):
        """
        Fetch corrections from Elasticsearch and cache them. Successive calls will overwrite the cache.

        Corrections are stored in flat dict using a lookup key generated from the match fields by _key().
        """
        self.corrections = {}
        try:
            client = Elasticsearch(self.es_uri, timeout=300)
            s = scan(client=client, index=self.es_index, doc_type=self.es_doc_type, scroll='10m')
            for doc in s:
                self._add_correction(doc)
        except ElasticsearchException as e:
            logger.error('unable to fetch corrections: {}'.format(e))
        else:
            logger.info('loaded {} corrections from {}/{}/{}'.
                        format(len(self.corrections),
                               self.es_uri,
                               self.es_index,
                               self.es_doc_type))

    def _key(self, doc):
        """
        Generate lookup key using the fields in the doc.

        :param dict doc: record document containing fields as keys
        """
        return '--'.join([str(doc.get(f,'__')) for f in self.match_fields])

    def _add_correction(self, doc):
        """
        Add correction to cache.

        :param dict doc: Elasticsearch document
        """
        source = doc.get('_source',{})
        ## make sure all the fields are there
        for field in self.match_fields:
            if field not in source:
                logger.warning('match field {} missing for correction document (id={})'.format(field,doc['_id']))
                return
        if self.source_field not in source:
                logger.warning('source field {} missing for correction document (id={})'.format(self.source_field,doc['_id']))
        ## add to cache using generated key
        self.corrections[self._key(source)] = source[self.source_field]

    def correct(self, rec):
        """
        Corrects fields in the raw JobUsageRecord. The record is mutated by correcting
        the appropriate field, and adding a new field named Raw<corrected field name>
        with the original value.

        :param dict rec: record document
        :return dict: record document
        """
        for field in self.match_fields:
            if field not in rec:
                return rec
        key = self._key(rec)
        if key in self.corrections:
            rec['Raw'+self.dest_field] = rec[self.dest_field]
            rec[self.dest_field] = self.corrections[key]
        return rec


if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings()
    logging.basicConfig(level=logging.INFO)
    c = Corrections(uri = 'https://gracc.opensciencegrid.org/q',
                    index = 'gracc.corrections',
                    doc_type = 'vo',
                    match_fields = ['VOName','ReportableVOName'],
                    source_field = 'CorrectedVOName',
                    dest_field = 'VOName')
