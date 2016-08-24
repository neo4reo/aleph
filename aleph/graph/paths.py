import logging

from aleph.core import db
from aleph.model import Path
from aleph.graph.nodes import NodeType
from aleph.graph.edges import EdgeType

log = logging.getLogger(__name__)

# Paths are cached because they take a long time to generate and thus browsing
# them via the UI would take minutes for each page load or filter to be
# applied. This is obviously not ideal, since it means the data is going PSQL
# -> Neo4J -> PSQL. That round trip is almost guaranteed to cause weird
# artifacts when upstream items are deleted or the graph has to be
# re-generated.


def generate_paths(graph, entity, ignore_types=['PART_OF', 'MENTIONS']):
    """Generate all possible paths which end in a different collection."""
    Path.delete_by_entity(entity.id)
    if graph is None or entity.state != entity.STATE_ACTIVE:
        return
    log.info("Generating graph path cache: %r", entity)
    # TODO: should max path length be configurable?
    q = "MATCH pth = shortestPath((start:Entity)-[*1..3]-(end:Entity)) " \
        "MATCH (start:Entity)-[startpart:PART_OF]->(startcoll:Collection) " \
        "MATCH (end:Entity)-[endpart:PART_OF]->(endcoll:Collection) " \
        "WHERE NOT (end)-[:PART_OF]->(startcoll) AND " \
        "startpart.alephCanonical = {entity_id} AND " \
        "all(r IN relationships(pth) WHERE NOT type(r) IN {ignore_types}) " \
        "RETURN DISTINCT pth, endcoll.alephCollection AS end_collection_id"
    count = 0
    for row in graph.run(q, entity_id=entity.id, ignore_types=ignore_types):
        path = row.get('pth')
        nodes = [NodeType.dict(n) for n in path.nodes()]
        edges = []
        for i, rel in enumerate(row.get('pth').relationships()):
            data = EdgeType.dict(rel)
            data['$source'] = rel.start_node().get('id')
            data['$target'] = rel.end_node().get('id')
            data['$inverted'] = data['$source'] != nodes[i]['id']
            edges.append(data)
        Path.from_data(entity, row.get('end_collection_id'), nodes, edges)
        count += 1
    db.session.commit()
    # TODO: send email to collection owners?
    log.info("Generated %s path for %r", count, entity)


def delete_paths(entity_id):
    """Delete the paths based on this entity."""
    Path.delete_by_entity(entity_id)
    db.session.commit()
