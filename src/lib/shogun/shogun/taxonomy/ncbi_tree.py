#!/usr/bin/env python
"""
This library was adapted from:
        https://github.com/luo-chengwei/utilitomics

This library works with the taxonomy db download from NCBI FTP:

ftp://ftp.ncbi.nih.gov:/pub/taxonomy/taxdump.tar.gz

basically you can init an taxonomy tree obj by:

t_tree = ncbi.NCBITree(path)   # tree being the tax dump db unzip dir
then you can basically get the taxonomy ranks using:

path = t_tree.get_name_path_with_taxon_id(taxon_id)

"""

import os
import networkx as nx
import csv

from shogun.utils.pickle_class import PickleClass
from shogun import SETTINGS


class NCBITree(PickleClass):
    def __init__(self, cache=True, _ncbi_taxdmp_dir=SETTINGS.ncbi_taxdmp_dir):
        super().__init__()
        self.tree = nx.DiGraph()
        # construct name -> taxon_id mapping
        self.name2taxon_id = {}
        self.taxon_id2name = {}

        # Private variables (should be set in settings)
        self._ncbi_taxdmp_dir = _ncbi_taxdmp_dir

        self._parse_ncbi_taxonomy()

        if cache:
            self.save()

    def _parse_ncbi_taxonomy(self):
        with open(os.path.join(self._ncbi_taxdmp_dir, 'names.dmp'), 'r') as handle:
            csv_handle = csv.reader(handle, delimiter="\t")
            for cols in csv_handle:
                taxon_id = cols[0]
                name = cols[2]
                self.name2taxon_id[name] = taxon_id
                if cols[-2] == 'scientific name':
                    self.taxon_id2name[taxon_id] = name

        # construct node tree
        edges = []
        nodes = {}
        with open(os.path.join(self._ncbi_taxdmp_dir, 'nodes.dmp'), 'r') as handle:
            csv_handle = csv.reader(handle, delimiter="\t")
            for cols in csv_handle:
                parent_node = cols[2]
                children_node = cols[0]
                rank = cols[4]
                nodes[children_node] = rank
                if children_node != parent_node:
                    edges.append((children_node, parent_node))

        self.tree.add_edges_from(edges)
        nx.set_node_attributes(self.tree, 'rank', nodes)

    def get_taxon_id_lineage_with_taxon_id(self, taxon_id):
        path = [taxon_id]
        current_node = taxon_id
        if current_node not in self.tree.nodes():
            return []
        while len(self.tree.successors(current_node)) > 0:
            path.append(self.tree.successors(current_node)[0])
            current_node = self.tree.successors(current_node)[0]
        return path

    def get_taxon_id_lineage_with_name(self, name):
        if name not in self.name2taxon_id:
            return []
        path = self.get_taxon_id_lineage_with_taxon_id(self.name2taxon_id[name])
        return path

    def get_name_lineage_with_taxon_id(self, taxon_id):
        taxon_id_lineage = self.get_taxon_id_lineage_with_taxon_id(taxon_id)
        name_lineage = []
        for x in taxon_id_lineage:
            rank = self.tree.node[x]['rank']
            try:
                name = self.taxon_id2name[x]
            except KeyError:
                name = ''
            name_lineage.append((name, rank))
        return name_lineage

    def get_name_lineage_with_name(self, name):
        if name not in self.name2taxon_id:
            return []
        path = self.get_name_lineage_with_taxon_id(self.name2taxon_id[name])
        return path

    def get_rank_with_taxon_id(self, taxon_id, rank):
        taxon_id_lineage = self.get_taxon_id_lineage_with_taxon_id(taxon_id)
        name_lineage = self.get_name_lineage_with_taxon_id(taxon_id)
        for tid, (name, x) in zip(taxon_id_lineage, name_lineage):
            if x == rank:
                return tid, name
        return None, None

    def get_name_at_rank(self, name, rank):
        if name not in self.name2taxon_id:
            return None, None
        return self.get_rank_with_taxon_id(self.name2taxon_id[name], rank)


def main():
    ncbi_tree = NCBITree()
    ncbi_tree.save()

if __name__ == '__main__':
    main()