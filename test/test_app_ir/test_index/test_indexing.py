import os, sys
sys.path.insert (0, os.path.abspath ('./'))
from app_ir.indexing.indexing import Indexing
from app_ir.preprocess.preprocess import Preprocessing
from app_api.db.db import MongoDB

import pytest, pymongo
from collections import defaultdict
from bson.objectid import ObjectId

db = MongoDB ('test')

##### TEST Indexing #####

@pytest.mark.indexingTest
@pytest.mark.skip
def test__parse ():
	'''
	Test: No vocabulary existing before.
	Test: No document vector before.
	'''
	tokens = [
		[
			['xx', 'yy', 'zz'],
			['xx', 'tt']
		],
		[
			['yy', 'yy', 'zz'],
			['zz', 'tt']
		],	
	]

	docIDs = [0,1]
	indexing = Indexing (db=db)

	try:
		postings = indexing._parse (tokens, docIDs)
		vocabulary = indexing.get_vocabulary ()

		exp_vocabulary = {
			'xx':  {'termid': 0, 'df': 1},
			'yy': {'termid': 1, 'df': 2},
			'zz': {'termid': 2, 'df': 2},
			'tt': {'termid': 3, 'df': 2},
		}

		assert len (exp_vocabulary) == len (vocabulary)
		for k,v in exp_vocabulary.items ():
			assert vocabulary[k]['termid'] == v['termid']
			assert vocabulary[k]['df'] == v['df']

		expected_postings = [
			[0, 0, 0], [1, 0, 1],[2, 0, 2],[0, 0, 3],[3, 0, 4],
			[1, 1, 0], [1, 1, 1], [2, 1, 2], [2, 1, 3], [3, 1, 4]
		]

		assert len (postings) == len (expected_postings)
		for a,b in zip (postings, expected_postings):
			assert len (a) == len (b)
			for c,d in zip (a, b):
				assert c == d

		expected_doc_vectors = [
			{'docid': 0, 'tf': [(0,2), (1,1), (2,1), (3,1)]},
			{'docid': 1, 'tf': [(1,2), (2,2), (3,1)]},
		]	
		doc_vectors = list (indexing._doc_vector_coll._coll.find ().sort ('docid', 1))	

		assert len (expected_doc_vectors) == len (doc_vectors)
		for a,b in zip (expected_doc_vectors, doc_vectors):
			assert a['docid'] == b['docid']
			assert len (a['tf']) == len (b['tf'])
			for c,d in zip (a['tf'], b['tf']):
				for e,f in zip (c,d):
					assert e == f
	except Exception as ex:
		print (ex)
		indexing._doc_vector_coll.drop ()
		assert False
	else:
		indexing._doc_vector_coll.drop ()	

@pytest.mark.indexingTest
@pytest.mark.skip
def test__parse2 ():
	'''
	Test:  Vocabulary exists before.
	Test:  document vectors exists before.
	'''

	prev_vocabulary = [		
		{'term': 'xx', 'termid': 0, 'df': 1},
		{'term': 'yy', 'termid': 1, 'df': 2},
		{'term': 'zz', 'termid': 2, 'df': 2},
		{'term': 'tt', 'termid': 3, 'df': 2},
		{'term': 'nn', 'termid': 4, 'df': 1},
		{'term': 'mm', 'termid': 5, 'df': 1}
	]

	prev_doc_vectors = [
		{'docid': 0, 'tf': [(0,1), (1,1), (2,3), (3,1)]},
		{'docid': 1, 'tf': [(2,2), (3,2), (4,1)]},
	]

	tokens = [
		[
			['xx', 'yy', 'zz'],
			['xx', 'tt']
		],
		[
			['yy', 'yy', 'zz'],
			['zz', 'tt', 'kk']
		],	
	]

	docIDs = [0,2]
	db.vocabulary_coll.insert_many (prev_vocabulary)
	db.contentvectors_coll.insert_many (prev_doc_vectors)
	indexing = Indexing (db=db)

	try:
		postings = indexing._parse (tokens, docIDs)
		vocabulary = indexing.get_vocabulary ()

		exp_vocabulary = {
			'xx':  {'termid': 0, 'df': 2},
			'yy': {'termid': 1, 'df': 4},
			'zz': {'termid': 2, 'df': 4},
			'tt': {'termid': 3, 'df': 4},
			'nn': {'termid': 4, 'df': 1},
			'mm': {'termid': 5, 'df': 1},
			'kk': {'termid': 6, 'df': 1},
		}

		assert len (exp_vocabulary) == len (vocabulary)
		for k,v in exp_vocabulary.items ():
			assert vocabulary[k]['termid'] == v['termid']
			assert vocabulary[k]['df'] == v['df']

		expected_postings = [
			[0, 0, 0], [1, 0, 1],[2, 0, 2],[0, 0, 3],[3, 0, 4],
			[1, 2, 0], [1, 2, 1], [2, 2, 2], [2, 2, 3], [3, 2, 4], [6,2,5]
		]

		assert len (postings) == len (expected_postings)
		for a,b in zip (postings, expected_postings):
			assert len (a) == len (b)
			for c,d in zip (a, b):
				assert c == d

		expected_doc_vectors = [
			{'docid': 0, 'tf': [(0,2), (1,1), (2,1), (3,1)]},
			{'docid': 1, 'tf': [(2,2), (3,2), (4,1)]},
			{'docid': 2, 'tf': [(1,2), (2,2), (3,1), (6,1)]},
		]

		doc_vectors = list (indexing._doc_vector_coll._coll.find ().sort ('docid', 1))	

		assert len (expected_doc_vectors) == len (doc_vectors)
		for a,b in zip (expected_doc_vectors, doc_vectors):
			assert a['docid'] == b['docid']
			assert len (a['tf']) == len (b['tf'])
			for c,d in zip (a['tf'], b['tf']):
				for e,f in zip (c,d):
					assert e == f
	except Exception as ex:
		print (ex)
		indexing._doc_vector_coll.drop ()
		indexing._vocabulary_coll.drop ()
		assert False
	else:
		indexing._doc_vector_coll.drop ()
		indexing._vocabulary_coll.drop ()

@pytest.mark.indexingTest
@pytest.mark.skip
def test__index ():
	postings = [
		[0, 0, 0], [1, 0, 1], [2, 0, 2], [0, 0, 3], [3, 0, 4], 
		[1, 1, 0], [1, 1, 1], [2, 1, 2], [2, 1, 3], [3, 1, 4]]

	b = Indexing (db=db)
	index = b._index (postings)
	expected_index = [
		[0, [[0, 2, 0, 3]]], [1, [[0, 1, 1], [1, 2, 0, 1]]],
		[2, [[0,1,2], [1, 2, 2, 3]]], [3, [[0,1,4], [1,1,4]]]
	]
	assert len (index) == len (expected_index)
	for j in range (4):
		i = index[j]
		ei = expected_index[j]
		assert i[0] == ei[0]
		assert len (i[1]) == len (ei[1])
		for k,t in zip (i[1], ei[1]):
			assert len (k) == len (t)
			for m in range (len (k)):
				assert k[m] == t[m]

@pytest.mark.indexingTest
@pytest.mark.skip
def test__update_indexes ():
	index = [
		[0, [[0, 2, 0, 3]]], 
		[1, [[0, 1, 1], [1, 2, 0, 1]]],
		[2, [[0,1,2], [1, 2, 2, 3]]], 
		[3, [[0,1,4], [1,1,4]]]
	]

	b = Indexing (db=db)
	try:
		b.update_indexes (index)
		fetched_index = b.fetch_indexes ([0,1,2,3])
		fetched_index = b._to_list_memory_indexes (fetched_index)
		assert len (fetched_index) == len (index)
		for j in range (4):
			i = fetched_index[j]
			ei = index[j]
			assert i[0] == ei[0]
			assert len (i[1]) == len (ei[1])
			for k,t in zip (i[1], ei[1]):
				assert len (k) == len (t)
				for m in range (len (k)):
					assert k[m] == t[m]

	except Exception as ex:
		print (ex)
		b._index_coll.drop ()
		assert False
	else:
		b._index_coll.drop ()

@pytest.mark.indexingTest
@pytest.mark.skip
def test__index_new_docs ():
	collection = [
		[0, [['xx', 'yy', 'zz'],['xx', 'tt']]],
		[1, [['yy', 'yy', 'zz'],['zz', 'tt']]],	
	]

	b = Indexing (db=db)
	index = b._index_new_docs (collection)

	expected_index = [
		[0, [[0, 2, 0, 3]]], [1, [[0, 1, 1], [1, 2, 0, 1]]],
		[2, [[0,1,2], [1, 2, 2, 3]]], [3, [[0,1,4], [1,1,4]]]
	]
	assert len (index) == len (expected_index)
	for j in range (4):
		i = index[j]
		ei = expected_index[j]
		assert i[0] == ei[0]
		assert len (i[1]) == len (ei[1])
		for k,t in zip (i[1], ei[1]):
			assert len (k) == len (t)
			for m in range (len (k)):
				assert k[m] == t[m]	

@pytest.mark.indexingTest
@pytest.mark.skip
def test__left_join_postings_lists ():
	# test if 
	pl = [[0, 1, 1], [3, 2, 0, 1]]
	target_pl = [[0,2,4,5], [2,1,10]]
	b = Indexing (db=db)
	pl = b._left_join_postings_lists (pl, target_pl)
	expected_pl = [[0, 1, 1], [2,1,10], [3, 2, 0, 1]]

	assert len (pl) == len (expected_pl)
	for k,m in zip (pl, expected_pl):
		assert len (k) == len (m)
		for t,n in zip (k,m):
			assert t == n

@pytest.mark.indexingTest
@pytest.mark.skip
def test__merge_indexes ():
	# Test cache indexes contains posting lists of docs that edited index does not have
	# Test cache indexes contains terms that edited index does not have
	# Test new indexes contains new terms.
	# Test next indexes contains existing terms.

	new_indexes = [
		[0, [[10, 2, 0, 3]]], 
		[1, [[11, 1, 1], [12, 2, 0, 1]]],
		[2, [[10,1,2], [12, 2, 2, 3]]], 
		[3, [[10,1,4], [13,1,4]]],
		[10, [[10,1,5], [13,1,5]]],
	]

	edited_indexes = [
		[0, [[0, 2, 0, 3]]], 
		[1, [[0, 1, 1], [1, 2, 0, 1]]],
		[2, [[0,1,2], [1, 2, 2, 3]]], 
		[3, [[0,1,4], [1,1,4]]]
	]

	cache_indexes = {
		1: [[0, 1, 6], [1, 2, 0, 20], [3, 1, 10]], 
		5: [[0, 1, 16]]
	}
	cache_indexes = defaultdict (lambda: None, cache_indexes)

	disk_indexes = [
		[0, [[0, 3, 10, 19]]], 
		[1, [[0, 1, 6], [1, 2, 0, 20]]],
		[2, [[0,1,5], [1, 2, 2, 7]]], 
		[3, [[0,1,4], [1,1,4]]], 
		[5, [[0, 1, 16]]]
	]
 		
	expected_index = [
		[0, [[0, 2, 0, 3], [10, 2, 0, 3]]], 
		[1, [[0, 1, 1], [1, 2, 0, 1], [3, 1, 10], [11, 1, 1], [12, 2, 0, 1]]],
		[2, [[0,1,2], [1, 2, 2, 3],[10,1,2], [12, 2, 2, 3]]], 
		[3, [[0,1,4], [1,1,4],[10,1,4], [13,1,4]]],
		[10, [[10,1,5], [13,1,5]]]
	]

	b = Indexing (db=db)
	b.save_indexes (disk_indexes)
	b._indexes = cache_indexes

	try:
		merged_indexes = b._merge_indexes (new_indexes, edited_indexes)
		assert len (merged_indexes) == len (expected_index)
		for j in range (len (merged_indexes)):
			i = merged_indexes[j]
			ei = expected_index[j]
			assert i[0] == ei[0]
			assert len (i[1]) == len (ei[1])
			for k,t in zip (i[1], ei[1]):
				assert len (k) == len (t)
				for m in range (len (k)):
					assert k[m] == t[m]

	except Exception as ex:
		print (ex)
		b._index_coll.drop ()
		assert False
	else:
		b._index_coll.drop ()	

@pytest.mark.indexingTest
@pytest.mark.skip
def test_index ():

	collection = [
		[0, 'xx yy zz. xx tt.', 1],
		[10, 'yy yy zz. zz tt kk.', 0],	
	]

	vocabulary = [		
		{'term': 'xx', 'termid': 0, 'df': 1},
		{'term': 'yy', 'termid': 1, 'df': 2},
		{'term': 'zz', 'termid': 2, 'df': 2},
		{'term': 'tt', 'termid': 3, 'df': 2},
		{'term': 'nn', 'termid': 4, 'df': 1},
		{'term': 'mm', 'termid': 5, 'df': 1}
	]

	disk_indexes = [
		[0, [[0,3,10,19]]], 
		[1, [[0,1,6], [1,2,0,20], [3,1,10]]],
		[2, [[0,1,5], [1,2,2,7]]], 
		[3, [[0,1,4], [1,1,4]]], 
		[4, [[0, 1, 16]]],
		[5, [[0, 1, 17]]],
	]

	cache_indexes = {
		1: [[0, 1, 6], [1, 2, 0, 20],[3,1,10]], 
		5: [[0, 1, 16]]
	}
	cache_indexes = defaultdict (lambda: None, cache_indexes) 

	expected_index = [
		[0, [[0,2,0,3]]], 
		[1, [[0,1,1], [1,2,0,20], [3,1,10], [10,2,0,1]]],
		[2, [[0,1,2], [1,2,2,7], [10,2,2,3]]], 
		[3, [[0,1,4], [1,1,4], [10,1,4]]],
		[4, [[0, 1, 16]]],
		[5, [[0, 1, 17]]],
		[6, [[10,1,5]]]
	]

	exp_vocabulary = {
		'xx':  {'termid': 0, 'df': 2},
		'yy': {'termid': 1, 'df': 4},
		'zz': {'termid': 2, 'df': 4},
		'tt': {'termid': 3, 'df': 4},
		'nn': {'termid': 4, 'df': 1},
		'mm': {'termid': 5, 'df': 1},
		'kk': {'termid': 6, 'df': 1},
	}

	preprocessing = Preprocessing ()
	b = Indexing (db=db, preprocessing=preprocessing)
	b._vocabulary_coll.insert_many (vocabulary)
	b._create_vocabulary_cache ()
	b.save_indexes (disk_indexes)
	b._indexes = cache_indexes
	
	try:
		b.index (collection)
		_vocabulary = b.get_vocabulary ()

		# test vocabulary
		assert len (_vocabulary) == len (exp_vocabulary)
		for k,v in _vocabulary.items ():
			assert v['termid'] == exp_vocabulary[k]['termid']
			assert v['df'] == exp_vocabulary[k]['df']

		fetched_index = b.fetch_indexes ([0,1,2,3,4,5,6])
		fetched_index = b._to_list_memory_indexes (fetched_index)

		# test indexes
		assert len (fetched_index) == len (expected_index)
		for j in range (len (fetched_index)):
			i = fetched_index[j]
			ei = expected_index[j]
			assert i[0] == ei[0]
			assert len (i[1]) == len (ei[1])
			for k,t in zip (i[1], ei[1]):
				assert len (k) == len (t)
				for m in range (len (k)):
					assert k[m] == t[m]

		# test document vectors

	except Exception as ex:
		print (ex)
		b._vocabulary_coll.drop ()
		b._index_coll.drop ()
		b._doc_vector_coll.drop ()
		assert False
	else:
		b._vocabulary_coll.drop ()
		b._index_coll.drop ()
		b._doc_vector_coll.drop ()		

##### TEST BSBIndexing #####

@pytest.mark.bsbindexingTest
@pytest.mark.skip
def test_bsbi_insert_block (): pass

@pytest.mark.bsbindexingTest
@pytest.mark.skip
def test_bsbi_merge_blocks ():
	index0 = [
		{'termid': 0, 'pl': [[0,1,0]]},
		{'termid': 1, 'pl': [[0,1,1], [1,1,5]]},
	]

	index1 = [
		{'termid': 0, 'pl': [[2,1,10]]},
		{'termid': 2, 'pl': [[2,2,5,100], [3,1,1]]},
	]

	index2 = [
		{'termid': 2, 'pl': [[4,1,11]]},
		{'termid': 3, 'pl': [[4,1,5], [5,1,1]]},
	]	

	index3 = [
		{'termid': 4, 'pl': [[6,1,6], [7,1,7]]},
		{'termid': 5, 'pl': [[8,1,6], [9,1,7]]}
	]

	b = BSBIndexing ('test')
	b.db[b.temp_index_coll_template.format (0)].insert_many (index0)
	b.db[b.temp_index_coll_template.format (2)].insert_many (index1)
	b.db[b.temp_index_coll_template.format (4)].insert_many (index2)
	b.db[b.temp_index_coll_template.format (6)].insert_many (index3)

	expected_index = [
		{'termid': 0, 'pl': [[0,1,0], [2,1,10]]},
		{'termid': 1, 'pl': [[0,1,1], [1,1,5]]},
		{'termid': 2, 'pl': [[2,2,5,100], [3,1,1], [4,1,11]]},
		{'termid': 3, 'pl': [[4,1,5], [5,1,1]]},
		{'termid': 4, 'pl': [[6,1,6], [7,1,7]]},
		{'termid': 5, 'pl': [[8,1,6], [9,1,7]]}
	]

	dnum = 8
	bsize_max = 2

	try:
		b._merge_blocks (dnum, bsize_max)
		index = list (b.index_coll.find ().sort ('termid', 1))		
		assert len (index) == len (expected_index)
		for j in range (len (index)):
			i = index[j]
			ei = expected_index[j]
			assert i['termid'] == ei['termid']
			assert len (i['pl']) == len (ei['pl'])
			for k,t in zip (i['pl'], ei['pl']):
				assert len (k) == len (t)
				for z in range (len (k)):
					assert k[z] == t[z]	
	except Exception as ex:
		print (ex)
		b.db[b.temp_index_coll_template.format (0)].drop ()
		b.db[b.temp_index_coll_template.format (2)].drop ()
		b.db[b.temp_index_coll_template.format (4)].drop ()
		b.db[b.temp_index_coll_template.format (6)].drop ()		
		b.index_coll.drop ()
		assert False
	else:
		b.index_coll.drop ()		


