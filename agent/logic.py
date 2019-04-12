#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 19 15:01:09 2017

@author: louiseadennis
"""

import copy

class logical_expression:
    
    def __init__(self, lhs, rhs, op):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op
        
    def logicalConsequence(self, unifier):
        if (self.op == 'not'):
            if not self.rhs.logicalConsequence(unifier).hasNext():
                return unif_iterator(unifier)
        elif (self.op == 'and'):
            left_iterator = self.lhs.logicalConsequence(unifier)
            iterator = and_iterator(left_iterator, self.rhs)
        else:
            return self.rhs.logicalConsequence(unifier)    
            
        return iterator
            
class unif_iterator:
    
    def __init__(self, unifier):
        self.unifier = unifier
        self.can_return = 1
        
    def hasNext(self):
        return self.can_return
    
    def get_next(self):
        if (self.can_return):
            return self.unifier
        else:
            return "NULL"
            
class and_iterator:
    
    def __init__(self, left_iterator, rhs):
        self.left_iterator = left_iterator
        self.rhs = rhs
        
        self.current = "NULL"
        self.right_iterator = "NULL"
        
    def hasNext(self):
        if (self.current == "NULL"):
            self.get()
        else:
            return not (self.current == "NULL")
        
    def get_next(self):
        if (self.current == "NULL"):
            self.get()
        tmp = self.current
        self.current = "NULL"
        return tmp
    
    def get(self):
        self.current == "NULL"
        while ( ( self.right_iterator == "NULL" or not self.right_iterator.hasNext() ) and self.left_iterator.hasNext() ):
            unifier_left = self.left_iterator.next()
            self.right_iterator = self.rhs.logicalConsequence(unifier_left)
            
        if ( ( not (self.right_iterator == "NULL") ) and self.right_iterator.hasNext()):
            self.current = self.right_iterator.next()
            
class belief_query:
    
    def __init__(self, beliefbase, query):
        self.beliefbase = beliefbase
        self.query = query
        
    def logicalConsequence(unifier):
        return belief_iterator(self.beliefbase, self.query, unifier)
        
class belief_iterator:
    
    def __init__(self, beliefbase, query, unifier):
        self.query = query
        self.current = "NULL"
        self.iterator = list_iterator(beliefbase[query['functor']])
        self.unifier = unifier
        
    def hasNext(self):
        if (self.current == "NULL"):
            self.get()
        else:
            return not (self.current == "NULL")
        
    def get_next(self):
        if (self.current == "NULL"):
            self.get()
        tmp = self.current
        self.current = "NULL"
        return tmp

    def get(self):
        if (self.query == 1):
            self.current = {}
        
        while self.iterator.hasNext():
            unifier_copy = copy.deepcopy(self.unifier)
            
            term = self.iterator.next()
            query_copy = copy.deepcopy(self.query)
            if (unifier_copy.unifies(term, query_copy)):
                self.current = unifier_copy
                break

class list_iterator:
    
    def __init__(self, list):
        self.list = list(list)
        
    def hasNext(self):
        return not (len(self.list) == 0)
    
    def get_next(self):
        return self.list.pop()
   
def isVar(term):
    return term['functor'][0].isupper()
    
class unifier:
    
    def __init__(self):
        self.unifier = {}
        
    def valueOf(self, var):
        return self.unifier['var']
    
    def has_value(self, var):
        return self.unifier.contains(var)
        
    def unifies(self, term1, term2):
        if (term1 == term2):
            return 1
        
        if (isVar(term1)):
            term1var = 1
        if (ifVar(term2)):
            term2var = 1
            
        if (term1var == 1 and not has_value(term1) or self.unifies(valueOf(term1), term2)):
            self.unifier[term1['functor']] == term2
            return 1
        
        if (term2var == 1 and not has_value(term2) or self.unifies(valueOf(term2), term1)):
            self.unifier[term2['functor']] == term1
            return 1
        
        if not (term1['functor'] == term2['functor']):
            return 0
        elif not len(term1['args']) == len(term2['args']):
            return 0
        else:
            unifier_copy = copy.deepcopy(self.unifier)
            for counter in range(0, len(term1['args'])):
                if not unifier_copy.unifies(term1['args'][counter], term2['args'][counter]):
                    return 0
            self.unifier = unifier_copy 
            return 1
        
        
        
        
        
            
        
