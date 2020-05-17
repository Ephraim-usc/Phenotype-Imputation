### import packages
import tskit
import tqdm
import numpy as np

### coalescent relationship matrix
def g(p):
  return 1/(p*(1-p))

def zeta(tree):
  N = tree.num_samples()
  rel_nodes = list(tree.nodes())
  zetas = np.zeros([N, N])
  for c in rel_nodes:
    descendants = list(tree.samples(c))
    n = len(descendants)
    if(n == 0 or n == N):
      continue
    q = (tree.time(tree.parent(c)) - tree.time(c)) * g(n / N)
    zetas[np.ix_(descendants, descendants)] += q
  zetas /= tree.total_branch_length
  return zetas

def epsilon(x):
  N = x.shape[0]
  mean = x.mean()
  colmean = np.tile(x.mean(axis = 0), (N, 1))
  rowmean = colmean.T
  return x + mean - colmean - rowmean

def getEK(tree):
  buffer = epsilon(zeta(tree, g))
  L = tree.total_branch_length
  return buffer/L

def getEK_trees(trees, flags = None, file = None):
  if (flags == None):
    flags = [True] * trees.num_trees
  elif len(flags) != trees.num_trees:
    print("incorrect flags length!")
  idx_trees = np.where(flags)[0].tolist()
  
  N = trees.num_samples
  EK = np.zeros([N, N])
  total_tl = 0
  pbar = tqdm.tqdm(total = len(idx_trees), 
                   bar_format = '{l_bar}{bar:30}{r_bar}{bar:-30b}',
                   miniters = len(idx_trees) // 100,
                   file = file)
  
  for i in idx_trees:
    tree = trees.at_index(i)
    interval = tree.interval
    tl = (interval[1] - interval[0]) * tree.total_branch_length * 1e-8
    total_tl += tl
    EK += getEK(tree) * tl
    pbar.update(1)
  EK /= total_tl
  pbar.close()
  return (EK, round(total_tl))

def get_flags(trees, variants, file = None):
    flags = [False] * trees.num_trees
    for v in tqdm.tqdm(variants, bar_format = '{l_bar}{bar:30}{r_bar}{bar:-30b}',
                       miniters = len(variants) // 100, 
                       file = file):
      flags[trees.at(v).index] = True
    return flags

def eGRM(trees, num = -1):
  N = trees.num_samples
  buffer = np.zeros([N, N])
  total_tl = 0
  for tree in trees.trees():
    #print(total_tl)
    tl = (tree.interval[1] - tree.interval[0]) * tree.total_branch_length * 1e-8
    total_tl += tl
    K = zeta(tree)
    #print(K[0, 0])
    buffer += K * tl
    num -= 1
    if num == 0:
      break
  buffer /= total_tl
  buffer = epsilon(zeta(tree, g))
  return buffer, total_tl

def eGRM_obs(trees, loci, num = -1):
  N = trees.num_samples
  total_tl = 0
  buffer = np.zeros([N, N])
  tree = trees.first()
  i = 0
  while i < len(loci):
    while tree.interval[0] >= loci[i]:
      i += 1
      if i >= len(loci):
        return buffer/total_tl, total_tl
    while tree.interval[1] < loci[i]:
      tree.next()
    tl = (tree.interval[1] - tree.interval[0]) * tree.total_branch_length * 1e-8
    total_tl += tl
    K = zeta(tree)
    buffer += K * tl; #print(str(tree.index) + " " + str(K[0, 0]))
    tree.next(); i += 1
    num -= 1
    if num == 0:
      break
  buffer = epsilon(zeta(tree, g))
  return buffer/total_tl, total_tl

  
  
  
#########

'''
def relevant_nodes(tree):
  N = tree.num_samples()
  rel_nodes = []
  for i in list(range(N)):
    c = i
    while not c in rel_nodes:
      if c == -1: 
        break
      rel_nodes.append(c)
      c = tree.parent(c)
  rel_nodes.sort()
  return rel_nodes
'''


'''
def affected_nodes(prev_tree, tree):
  buffer = []
  for node in set(prev_tree.nodes()).union(set(tree.nodes())):
    if prev_tree.parent(node) != tree.parent(node):
      buffer.append(node)
    elif sorted(list(prev_tree.samples(node))) != sorted(list(tree.samples(node))):
      buffer.append(node)
  buffer = list(set(buffer))
  return buffer

def zeta_rec(prev_K, tree, prev_tree = None):
  N = tree.num_samples()
  if prev_tree == None:
    tree.prev(); prev_tree = tree.copy(); tree.next()
  K = prev_K * prev_tree.total_branch_length
  affected = affected_nodes(prev_tree, tree)
  
  for node in affected:
    descendants = list(prev_tree.samples(node))
    n = len(descendants)
    if(n == 0 or n == N):
      continue
    time = prev_tree.time(prev_tree.parent(node)) - prev_tree.time(node)
    q = g(n / N)
    K[np.ix_(descendants, descendants)] -= q * time
  
  for node in affected:
    descendants = list(tree.samples(node))
    n = len(descendants)
    if(n == 0 or n == N):
      continue
    time = tree.time(tree.parent(node)) - tree.time(node)
    q = g(n / N)
    K[np.ix_(descendants, descendants)] += q * time
  
  K /= tree.total_branch_length
  return K

def EGRM(trees, num = -1):
  N = trees.num_samples
  buffer = np.zeros([N, N])
  total_tl = 0
  for tree in trees.trees():
    #print(total_tl)
    tl = (tree.interval[1] - tree.interval[0]) * tree.total_branch_length * 1e-8
    total_tl += tl
    K = zeta(tree)
    #print(K[0, 0])
    buffer += K * tl
    num -= 1
    if num == 0:
      break
  buffer /= total_tl
  return buffer, total_tl

def EGRM_rec(trees, num = -1):
  N = trees.num_samples
  buffer = np.zeros([N, N])
  tree = trees.first()
  K = zeta(tree)
  total_tl = (tree.interval[1] - tree.interval[0]) * tree.total_branch_length * 1e-8
  while tree.next():
    tl = (tree.interval[1] - tree.interval[0]) * tree.total_branch_length * 1e-8
    total_tl += tl
    K = zeta_rec(K, tree)
    buffer += K * tl
    num -= 1
    if num == 0:
      break
  buffer /= total_tl
  return buffer, total_tl
'''

'''
def EGRM_obs(trees, loci, num = -1):
  N = trees.num_samples
  total_tl = 0
  buffer = np.zeros([N, N])
  tree = trees.first()
  i = 0
  while i < len(loci):
    while tree.interval[0] >= loci[i]:
      i += 1
      if i >= len(loci):
        return buffer/total_tl, total_tl
    while tree.interval[1] < loci[i]:
      tree.next()
    tl = (tree.interval[1] - tree.interval[0]) * tree.total_branch_length * 1e-8
    total_tl += tl
    K = zeta(tree)
    buffer += K * tl; #print(str(tree.index) + " " + str(K[0, 0]))
    tree.next(); i += 1
    num -= 1
    if num == 0:
      break
  return buffer/total_tl, total_tl

def EGRM_obs_rec(trees, loci, num = -1):
  N = trees.num_samples
  buffer = np.zeros([N, N])
  tree = trees.first()
  i = 0
  while tree.interval[1] < loci[i]:
    tree.next()
  tl = (tree.interval[1] - tree.interval[0]) * tree.total_branch_length * 1e-8
  total_tl = tl
  K = zeta(tree); buffer += K * tl; #print(str(tree.index) + " " + str(K[0, 0]))
  prev_tree = tree.copy(); i += 1
  while i < len(loci):
    while tree.interval[0] >= loci[i]:
      i += 1
      if i >= len(loci):
        return buffer/total_tl, total_tl
    while tree.interval[1] < loci[i]:
      tree.next()
    tl = (tree.interval[1] - tree.interval[0]) * tree.total_branch_length * 1e-8
    total_tl += tl
    K = zeta_rec(K, tree, prev_tree = prev_tree); buffer += K * tl; #print(str(tree.index) + " " + str(K[0, 0]))
    prev_tree = tree.copy()
    tree.next(); i += 1
    num -= 1
    if num == 0:
      break
  return buffer/total_tl, total_tl




def TMRCA(tree):
  N = tree.num_samples()
  rel_nodes = np.array(relevant_nodes(tree))
  times = [tree.time(node) for node in rel_nodes]
  rel_nodes = rel_nodes[np.flip(np.argsort(times))]
  tmrca = np.zeros([N, N])
  for c in rel_nodes:
    descendants = list(tree.samples(c))
    n = len(descendants)
    if(n == 0 or n == N):
      continue
    q = tree.time(c)
    tmrca[np.ix_(descendants, descendants)] = q
  return tmrca

def compare(trees1, trees2, n = 100):
  l = min(trees1.last().interval[1], trees2.last().interval[1])
  loci = np.random.randint(0, l, n)
  loci.sort()
  diffs = []
  for locus in loci:
    tree1 = trees1.at(locus)
    tree2 = trees2.at(locus)
    tmrca1 = TMRCA(tree1)
    tmrca2 = TMRCA(tree2)
    tmrca1 /= tmrca1.mean()
    tmrca2 /= tmrca2.mean()
    diff = np.abs(tmrca2 - tmrca1).mean()
    #print("at " + str(locus) + " diff " + str(diff))
    diffs.append(diff)
  return diffs 
'''
