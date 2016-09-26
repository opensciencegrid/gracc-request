import logging
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan
from elasticsearch.exceptions import ElasticsearchException

logger = logging.getLogger(__name__)

class Corrections:
    def __init__(self, elasticsearch_uri, index):
        self.vos = {}
        self.projects = {}
        try:
            client = Elasticsearch(elasticsearch_uri, timeout=300)
            s = scan(client=client, index=index, scroll='10m')
            for doc in s:
                type = doc.get('_type')
                source = doc.get('_source',{})
                if type == 'vo' \
                   and 'VOName' in source \
                   and 'ReportableVOName' in source \
                   and 'CorrectedVOName' in source:
                    self.vos[str(source['VOName'])+str(source['ReportableVOName'])] = source['CorrectedVOName']
                elif type == 'project' \
                     and 'ProjectName' in source \
                     and 'CorrectedProjectName' in source:
                    self.projects[str(source['ProjectName'])] = source['CorrectedProjectName']
        except ElasticsearchException as e:
            logger.error('unable to fetch corrections: {}'.format(e))
        else:
            logger.info('loaded {} vo and {} project name corrections from {}/{}'.
                        format(len(self.vos),
                               len(self.projects),
                               elasticsearch_uri,
                               index))

    def correct_vo(self, vo_name, reportable_vo_name):
        """
        Returns corrected VO name, or vo_name if there is no correction.
        """
        return self.vos.get(str(vo_name)+str(reportable_vo_name), vo_name)

    def correct_project(self, project_name):
        """
        Returns corrected project name, or project_name if there is no correction.
        """
        return self.projects.get(str(project_name), project_name)

    def correct(self, rec):
        """
        Corrects fields in the raw JobUsageRecord.
        """
        if 'VOName' in rec and 'ReportableVOName' in rec:
            rec['VOName'] = self.correct_vo(rec['VOName'], rec['ReportableVOName'])
        if 'ProjectName' in rec:
            rec['ProjectName'] = self.correct_project(rec['ProjectName'])

if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings()
    logging.basicConfig(level=logging.INFO)
    c = NameCorrections(elasticsearch_uri = 'https://gracc.opensciencegrid.org/q',
                        index = 'gracc.corrections')
