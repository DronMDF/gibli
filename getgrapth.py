#!/usr/bin/env python3

import pygit2

class Revision:
	def __init__(self, commit, deep, branch):
		self.commit = commit
		self.deep = deep
		self.branch = branch

repo = pygit2.Repository('.git')

commits = dict()
branches = {repo.head.target: (0, 0)}

for c in repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL):
	deep, branch = branches.pop(c.id)
	#print (c.id, c.parent_ids, deep, branch)
	if deep < 100:
		commits[c.id] = Revision(c, deep, branch)
	bb = {b[1] for b in branches.values()}
	for pn in c.parent_ids:
		bn = next((b for b in range(5000) if b not in bb))
		#print(pn, deep + 1, bn)
		if pn in branches:
			branches[pn] = max(branches[pn][0], deep + 1), branches[pn][1]
		else:
			branches[pn] = deep + 1, bn
			bb.add(bn)

print(len(commits))

