#!/usr/bin/env python3

import itertools
from pygit2 import Repository, GIT_SORT_TOPOLOGICAL, Oid

class Rev:
	def __init__(self, commit, deep):
		self.id = commit.id
		self.parent_ids = commit.parent_ids
		self.deep = deep

repo = Repository('.git')

def walker(oid):
	# Этот метод обхода оказался самым быстрым.
	# Но порядок выдачи удручает, поэтому ходим только по первым родителям
	# А ветки анализируем сами.
	# 50к коммитов проходят за 1.7с
	w = repo.walk(oid)
	w.simplify_first_parent()
	return w

commits = {commit.id: Rev(commit, deep) for deep, commit in enumerate(walker(repo.head.target))}

# берем непервых родителей и начинаем раскручивать ветки оттуда
branch_heads = [(p, r.id) for r in commits.values() for p in r.parent_ids[1:] if r.deep < 1000]

def deep_propagator(id, deep):
	def deep_generator(id, deep):
		if id in commits and commits[id].deep < deep:
			commits[id].deep = deep
			yield from commits[id].parent_ids
	todo = [id]
	for d in range(deep, 10000):
		todo = list(itertools.chain.from_iterable(deep_generator(id, d) for id in todo))
		if not todo:
			break

while branch_heads:
	bh, br = branch_heads.pop(0)
	bd = commits[br].deep + 1
	if bh in commits:
		deep_propagator(bh, bd)
		continue
	if bd > 1000:
		continue
	for deep, commit in enumerate(walker(bh), bd):
		rev = Rev(commit, deep)
		commits[rev.id] = rev
		if any((p in commits for p in rev.parent_ids)):
			for p in rev.parent_ids:
				if p not in commits:
					if deep < 1000:
						branch_heads.append((p, rev.id))
				else:
					deep_propagator(p, deep + 1)
			break

for c in commits.values():
	if len(c.parent_ids) > 1 and c.deep < 1000:
		c.deep = max((commits[p].deep - 1 for p in c.parent_ids if p in commits))
		for p in c.parent_ids:
			deep_propagator(p, c.deep + 1)

print('before cleanup:', len(commits), max((r.deep for r in commits.values())))

outofscope = [r.id for r in commits.values() if r.deep > 1000]
for o in outofscope:
	del commits[o]

print('after cleanup', len(commits), max((r.deep for r in commits.values())))
