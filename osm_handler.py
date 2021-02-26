import osmium as osm


class OSMHandler(osm.SimpleHandler):
    def __init__(self):
        super(OSMHandler, self).__init__()
        self.nodes = []
        self.ways = []
        self.relations = []
        # self.data = []

    # It seems .data never used
    # in a test, remove this make 60% speed increase. (108s -> 41s)

    # def tag_inventory(self, elem, elem_type):
    #     for tag in elem.tags:
    #         self.data.append([elem_type,
    #                           elem.id,
    #                           elem.version,
    #                           elem.visible,
    #                           pd.Timestamp(elem.timestamp),
    #                           elem.uid,
    #                           elem.user,
    #                           elem.changeset,
    #                           len(elem.tags)])

    def node(self, n):
        # self.tag_inventory(n, "node")
        self.nodes.append(["node", n.id, n.location])

    def way(self, w):
        # self.tag_inventory(w, "way")
        info = {}
        waypoints = []
        for tag in w.tags:
            info.update({(tag.k, tag.v)})
        for node in w.nodes:
            waypoints.append(node.ref)
        self.ways.append([w.id, waypoints, info])
        # print(w)

    def relation(self, r):
        # self.tag_inventory(r, "relation")
        if 'name' in r.tags:
            if 'NFTA' in r.tags['name']:
                if "Metro Rail" not in r.tags['name']:
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