import osmium as osm


class OSMHandler(osm.SimpleHandler):
    min_lat = 42
    max_lat = 43.5
    min_lon = -79.75
    max_lon = -78

    def __init__(self):
        osm.SimpleHandler.__init__(self)
        self.node_table = {}
        self.ways = []
        self.relations = []
        self.way_table = {}
        self.way_tag_table = {}

    def node(self, n):
        # self.tag_inventory(n, "node")
        if self.min_lat <= n.location.lat <= self.max_lat and self.min_lon <= n.location.lon <= self.max_lon:
            self.node_table.update({n.id: [n.location.lat, n.location.lon]})

    def way(self, w):
        # self.tag_inventory(w, "way")
        self.way_table.update({w.id: [node.ref for node in w.nodes]})
        self.way_tag_table.update({w.id: {tag.k: tag.v for tag in w.tags}})

    def relation(self, r):
        # self.tag_inventory(r, "relation")
        if 'name' in r.tags:
            if 'NFTA' in r.tags['name'] and "Metro Rail" not in r.tags['name']:
                info = {}
                waypoints = []
                for tag in r.tags:
                    info.update({(tag.k, tag.v)})
                for node in r.members:
                    waypoints.append(node.ref)
                    # waypoints.append(node)
                    # print('{},{},{}'.format(node.ref, node.role, node.type))
                self.relations.append([r.id, waypoints, info])
                # print(r.tags['name'])
