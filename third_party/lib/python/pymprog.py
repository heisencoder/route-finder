#**************************************************************************
#Copyright (C) 2009 Yingjie Lan, ylan@umd.edu

#This file is part of PyMathProg.

#PyMathProg is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 3 of the License, or
#(at your option) any later version.

#PyMathProg is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with PyMathProg. If not, see <http://www.gnu.org/licenses/>.
#**************************************************************************

def pymprog_version():
    return "pymprog 0.4.2"

def extract_keys(kd, kt):
    ed = {}
    for key in kt:
        if key in kd: 
           ed[key]=kd[key]
    return ed

#import glpk
from glpk import LPX
from glpk import env

_pyglpk_version_incompat = """
pyglpk version  incompatible!
Please get the latest version of pyglpk from
http://sourceforge.net/projects/pymprog/"""

try:
   from glpk import pyglpk_version
except: 
   raise Exception, _pyglpk_version_incompat
   
if pyglpk_version < '0.3.2':
   raise Exception, _pyglpk_version_incompat

#keep a GLOBAL list of models:
#only for implementation of the global interface.
_models = []

#Global interface:
#This allows one to create, manipulate, solve
#A model without explicitly deal with a model instance.
#Rather, the package manages the model instance.

def beginModel(name=None):
   """Start a model to work with."""
   prob = model(name)
   _models.insert(0,prob)

def endModel():
   """Finish with a model, model instance is returned."""
   return _models.pop(0)

def verbose(v):
   """Report what's going on."""
   _models[0].verb = v

def listmod():
   print "models (first is current):"
   for p in _models:
      print p.name, p

def st(cons, name=None, inds=None):
   """Create new constraints."""
   prob = _models[0]
   return prob.st(cons, name, inds)

def minimize(obj, name=None):
   """Create a minimizing objective."""
   prob = _models[0]
   prob.min(obj, name)

def maximize(obj, name=None):
   """Create a maximizing objective."""
   prob = _models[0]
   prob.max(obj, name)

def var(inds=None, name=None, kind=None, bounds=None):
   """Create variables over the given indices.
      you can optionally specify variable name,
      kind (default is float, other values: int, bool.
      bounds (default: (0, None) -- None = infinity)"""
   prob = _models[0]
   return prob.var(inds, name, kind, bounds)

def par(val, name=None):
   """Create parameters. the returned parameter
container has the same structure and index as 
the passed in values."""
   prob = _models[0]
   return prob.par(val, name)

def solve(t=None):
   """Solve the model, return solver status."""
   prob = _models[0]
   return prob.solve(t)

def solveMIP():
   """Solve the model using only MIP methods,
assuming you have solved the LP relaxation.
return solver status."""
   prob = _models[0]
   return prob.solveMIP()

def status():
   """obtain the status of the solver."""
   prob = _models[0]
   return prob.status()

def kkt(kind=None):
   """Karush-Kuhn-Tucker optimality conditions for 
1. a basic (simplex) solution if kind = float.  
   If the argument 'scaled' is true, return results
   of checking the internal scaled instance of the LP instead.
2. a mixed-integer solution if kind = int.  
   Note that only the primal components
   of the KKT object will have meaningful values.
"""
   prob = _models[0]
   return prob.kkt(kind)

def reportKKT(kind=None):
   """produce a convenient report on KKT"""
   prob = _models[0]
   return prob.reportKKT(kind)

def vobj():
   """obtain the objective value."""
   prob = _models[0]
   return prob.vobj()

def solvopt(**kwds):
   """add/get/del solver options. 
Only accept keyword arguments.
add: solvopt(method='exact');
get: solvopt();
del: solvopt(method=None);"""
   prob = _models[0]
   return prob.solvopt(**kwds)

def evaluate(expr):
   """return the value of an expression
when all its variables take their primal values."""
   return expr.evaluate() if isinstance(expr, parex)\
      else expr.primal if isinstance(expr, variable)\
      else expr.value if isinstance(expr, param)\
      else expr #unchanged

def sensit(file_name):
   """write sensitivity analysis report to a file"""
   prob = _models[0]
   prob.sensit(file_name)

def write(**kwds):
   """write specific information to files."""
   prob = _models[0]
   prob.write(**kwds)
   
####### Class Definitions ####

#below is how to do mixed indexing with dictionary
# x = {(3,'h'):6, (5,'k'):5}
# x[3,'h']

class iprod(object): 
   """index product: given a list/tuple of sets, 
   enumerate all combinations as tuples."""
   def __init__(self, *args): 
      self._llist =  args
      self._sofar = []

   def __iter__(self): 
      return self.next() 

   def next(self): 
      for idx in self._llist[len(self._sofar)]:
         self._sofar.append(idx)
         if len(self._sofar)==len(self._llist):
            yield tuple(self._sofar)
         else:
            for v in self.next(): yield v
         self._sofar.pop()

   def __len__(self):
       ret = 1
       for i in self._llist: ret *= len(i)
       return ret

class model(object):
   """this object holds an glpk.LPX() object.
    you can retrieve it by the "solver()" method.
    for how to use that object to solve models,
    you can refer to PyGLPK documentation.
    Once the model is solved, you can access
    the results via that object. You can also 
    access the solution by the variables created
    via the "var()" method, or find out the 
    status of the constraints by the constraints
    created by the "st()" method."""
   def __init__(me, name):
      me.p = LPX()
      me.p.name = name
      me.grid = 0 #group row id
      me.gcid = 0 #group col id
      me.gpid = 0 #group par id
      me.verb = False
      me.options = {} #solver options


   def var(me, inds=None, name=None, kind=None, bounds=None):
      if name==None:
         name = "X%d"%me.gcid
         me.gcid += 1
      if inds==None:
         idx = me.p.cols.add(1)
         return variable(me.p.cols[idx], name, kind, bounds) 
      #create many variables as a dict.
      vars = {}
      for t in inds: vars[t] = None
      idx = me.p.cols.add(len(vars))
      name += "[%s]"
      for t in vars:
         vars[t] = variable(me.p.cols[idx], 
            name%str(t), kind, bounds)
         idx += 1
      return vars

   def par(me, val, name=None):
      if name==None:
         name = "P%d"%me.gpid
         me.gpid += 1
      if type(val) in (int, long, float, str):
         return param(val, name)
      if type(val) in (list, tuple):
         return [me.par(v, "%s[%d]"%(name,i)) for 
           v,i in zip(val, range(len(val)))]
      if type(val) == dict: 
         pp = {}; name += "[%s]"
         for t in val: 
            pp[t] = me.par(val[t], name%str(t))
         return pp
      #assume to be something iterable (generator, set, ...):
      #however, if v is a string, umlimited recursion results
      return me.par([v for v in val], name) 

   def st(me, cons, name=None, inds=None):
      """subject to: add one or many constraints"""
      if name==None: 
         name="R%d"%me.grid
         me.grid += 1
      if type(cons) in (constraint, variable): 
            idx = me.p.rows.add(1)
            cons = cons.bind(me.p.rows[idx], name)
            if me.verb: print cons
            return cons
      cons = [t for t in cons] #copy
      if not cons: return cons #empty
      coni = xrange(len(cons))
      if inds==None: inds = xrange(len(cons))
      #create many constraints
      name += "[%s]"
      idx = me.p.rows.add(len(cons))
      for t, i in zip(inds, coni):
         cons[i] = cons[i].bind(me.p.rows[idx], name%str(t))
         if me.verb: print cons[i]
         idx += 1
      return cons

   def objcoef(me, expr):
      for i,c in expr.mat:
         me.p.obj[i] = c
      me.p.obj[None] = expr.const #linexp

   def max(me, expr, name=None):
      me.fobj(True, expr, name)

   def min(me, expr, name=None):
      me.fobj(False, expr, name)

   def fobj(me, maximize, expr, name):
      me.p.obj.maximize = maximize
      me.p.obj.name = name
      if type(expr) is variable:
         expr = +expr #convert to expression
      if type(expr) is not parex:
         raise Exception, "bad objective type"
      objective(expr).bind(me)
      if me.verb:
         name = '' if name==None else name
         impr = "MAX" if maximize else "MIN"
         print "%s '%s':"%(impr, name),
         print expr

   kind = property(lambda me: me.p.kind)

   def status(me): return me.p.status

   def nint(me): 
      """Get number of integer variables."""
      return me.p.nint()

   def nbin(me): 
      """Get number of binary variables."""
      return me.p.nbin()

   def solve(me, t=None):
       """you can change parameters, then the model will
rebuild itself before actually solve."""
       param.updateAll() #this takes care of rebuilding
       ret = {}
       meth=me.options.get('method')
       if meth == 'interior':
          ret[meth] = me.p.interior()
       elif meth == 'exact':
          ret[meth] = me.p.exact()
       else: 
          keywds=("msg_lev", "meth", "pricing", 
          "r_test", "tol_bnd", "tol_dj", "tol_piv",
          "obj_ll", "obj_ul", "it_lim", "tm_lim", 
          "out_frq", "out_dly", "presolve") 
          keywds=extract_keys(me.options, keywds)
          ret['simplex'] = me.p.simplex(**keywds)

       if t==None: t=me.kind
       if t != int: return ret
       meth=me.options.get('integer')
       ret[meth] = me.solveMIP()
       return ret

   def solveMIP(me):
       """Solve the model using only MIP methods,
assuming you have solved the LP relaxation.
return solver status."""
       meth=me.options.get('integer')
       if meth == 'advanced':
          return me.p.intopt()
       else: 
          #note: if your glpk version is too old,
          #some options might not be supported.
          keywds=("msg_lev", "br_tech", "bt_tech",
          "pp_tech", "gmi_cuts", "mir_cuts", 
          "tol_int", "tol_obj", "tm_lim", "out_frq", 
          "out_dly", "callback")
          keywds=extract_keys(me.options, keywds)
          return me.p.integer(**keywds)

   def kkt(me, kind=None):
      """Karush-Kuhn-Tucker optimality conditions for 
1. a basic (simplex) solution if kind = float.  
   If the argument 'scaled' is true, return results
   of checking the internal scaled instance of the LP instead.
2. a mixed-integer solution if kind = int.  
   Note that only the primal components
   of the KKT object will have meaningful values.
"""
      if kind is None: kind = me.kind
      return me.p.kkt() if kind is float else\
             me.p.kktint()

   def reportKKT(me, kind=None):
      """produce a convenient report on KKT"""
      if kind is None: kind = me.kind
      res = me.kkt(kind)
      rpt = """
Karush-Kuhn-Tucker optimality conditions:
=========================================

1) Error in Primal Solutions:
-----------------------------
Largest absolute error: %f (row id: %s)
Largest relative error: %f (row id: %s)
Quality of primal solution: %s

2) Error in Satisfying Primal Bounds:
-------------------------------------
Largest absolute error: %f (var id: %s)
Largest relative error: %f (var id: %s)
Quality of primal feasibility: %s
"""%( res.pe_ae_max, res.pe_ae_row, 
      res.pe_re_max, res.pe_re_row,
      res.pe_quality,
      res.pb_ae_max, res.pb_ae_ind,
      res.pb_re_max, res.pb_re_ind,
      res.pb_quality)
      if kind is int: return rpt
      return rpt + """
3) Error in Dual Solutions:
-----------------------------
Largest absolute error: %f (col id: %s)
Largest relative error: %f (col id: %s)
Quality of dual solution: %s

4) Error in Satisfying Dual Bounds:
-------------------------------------
Largest absolute error: %f (var id: %s)
Largest relative error: %f (var id: %s)
Quality of dual feasibility: %s
"""%( res.de_ae_max, res.de_ae_col, 
      res.de_re_max, res.de_re_col,
      res.de_quality,
      res.db_ae_max, res.db_ae_ind,
      res.db_re_max, res.db_re_ind,
      res.db_quality)

   def vobj(me): 
      """value of the objective."""
      return me.p.obj.value

   def scale(me, doit=True): 
      """scale or unscale the problem."""
      if doit: me.p.scale()
      else: me.p.unscale()


   def solvopt(me, **kwds):
      """add/get/del solver options. 
Only accept keyword arguments.
add: solvopt(method='exact');
get: solvopt();
del: solvopt(method=None);"""
      for opt in kwds:
          if kwds[opt] is not None:
             me.options[opt]=kwds[opt]
          elif opt in me.options:
             del me.options[opt]
      if len(kwds)==0: return me.options


   def sensit(me, file_name):
      """write sensitivity report to a file"""
      me.write(sens_bnds=file_name)

   def write(me, **kwds):
      """Output data about the linear program into a file with a given
    format.  What data is written, and how it is written, depends
    on which of the format keywords are used.  Note that one may
    specify multiple format and filename pairs to write multiple
    types and formats of data in one call to this function.
    
    mps       -- For problem data in the fixed MPS format.
    bas       -- The current LP basis in fixed MPS format.
    freemps   -- Problem data in the free MPS format.
    cpxlp     -- Problem data in the CPLEX LP format.
    glp       -- Problem data in the GNU LP format.
    prob      -- Problem data in a plain text format.
    sol       -- Basic solution in printable format.
    sens_bnds -- Bounds sensitivity information.
    ips       -- Interior-point solution in printable format.
    mip       -- MIP solution in printable format.
"""
      me.p.write(**kwds)


class _dirt_(object):
   """The base class for variable, parameter, parex.
The main functionality is to provide numerical type support,
so that the subclasses can be operated by operators like
'+', '-', '*', '/', '**'."""

   def _bad_type(me, b):
       global _good_types
       return type(b) not in _good_types

   def __add__(me, b):
       if me._bad_type(b): return NotImplemented
       return parex(me, '+', b)

   def __radd__(me, b):
       if me._bad_type(b): return NotImplemented
       return parex(me, '+', b)

   def __mul__(me, b):
       if me._bad_type(b): return NotImplemented
       return parex(me, '*', b)

   def __rmul__(me, b):
       if me._bad_type(b): return NotImplemented
       return parex(me, '*', b)

   def __sub__(me, b):
       if me._bad_type(b): return NotImplemented
       return parex(me, '-', b)

   def __rsub__(me, b): # b - me
       if me._bad_type(b): return NotImplemented
       return parex(b, '-', me)

   def __div__(me, b):
       if me._bad_type(b): return NotImplemented
       return parex(me, '/', b)

   def __rdiv__(me, b): #since me could be a const
       if me._bad_type(b): return NotImplemented
       return parex(b, '/', me)

   def __pos__(me): 
       return parex(0, 'ps', me)

   def __neg__(me):
       return parex(0, 'ng', me)

   def __pow__(me, b):
       return parex(me, '**', b)

def isConst(b):
       if type(b) in (int, float, long, param): 
          return True
       if isinstance(b, parex): 
          return b.isConst()
       return not isinstance(b, variable)
 
class param(_dirt_):
   """A parameter, whose value may be changed,
When a parameter changed in value, it will 
add it self to the class owned dirty list.
Each param also maintains its own list of listeners. 
The listeners can be parex or variable objects.
A class method is also provided to fire off the
updating process.
"""

   #another design may put this field under
   #a model instance, which makes sense if
   #a param must belong to a model instance.
   #We don't enforce that, and allow a param
   #to play in many models simultaneously.
   dirtyset = set() #class member

   @classmethod
   def updateAll(cls):
      updated = set() #update only once
      for p in cls.dirtyset:
         p.updateClients(updated)
      cls.dirtyset = set()
      return updated

   def __init__(me, val=None, name=None):
      if type(val) not in (int, float):
        raise Exception, "Bad parameter value!"
      me._val = val
      me.name = name
      me.clients = set() #for dirt

   def updateClients(me, updated):
      for c in me.clients:
         if c not in updated:
            c.update() #batchid
            updated.add(c)

   def register(me, client):
      """register as clients/listeners."""
      me.clients.add(client)

   def unregister(me, client):
      """unregister as clients/listeners."""
      me.clients.discard(client)

   def set_value(me, val): 
       if val == me._val: return
       me._val = val
       me.dirtyset.add(me)

   def get_value(me): return me._val
   value = property(get_value, set_value)

   def __repr__(me): 
      return "%s=%s"%(me.name,str(me._val))

class variable(_dirt_):
   """Represents a variable. 
Set bounds using x.bounds = (A, B) for x in [A,B].
If A or B is an expression containing parameters, 
then parameters changes will update the bounds.
To fix a variable at constant C, use x.bounds=(C,C).
Another easier way to set bounds: A <= x <= B.

Note: it is OK to use the st call to set a constraint
like this: st( A <= x <= B).
Basically, a variable is passed to st(), then 
st() converts it into an expression '0+x', and
then use the bounds on x to construct the constraint,
So be ware of the side effect: 
(1) the bounds on x changed and more subtly 
(2) the constraint is surely redundant as the
    bounds on x effectly ensures the same thing.
To ensure you bounds won't be modified by such 
constraints, it is recommended to set bounds of x 
after all constraints. Or, you can equivalently 
write: st(0 <= x - A <= B-A).
"""

   def __init__(me, col, name=None, kind=None, bounds=None):
       if kind==None: kind=float
       if bounds==None: bounds = 0, None
       me.x = col
       me._bexp = (0, None) #bound expression
       me.set_bounds(bounds)
       col.name = name
       #note: if kind=bool, then bounds<-(0,1)
       col.kind = kind #must follow set_bounds

   def check_bexp(me, lh):
      if lh is None: return
      if me._bad_type(lh):
         raise Exception, "Bad bound type!"
      if not isConst(lh):
         raise Exception, "Bound not constant!"

   def get_bounds(me): return me.x.bounds
   def set_bounds(me, b): 
      """If b is a parex containing param instances,
me must register to those params."""
      if b is None: b = 0, None
      for i in b: me.check_bexp(i)
      for p in me._depends(): 
         p.unregister(me)
      me._bexp = b
      for p in me._depends(): 
         p.register(me)
      me.update()

   bounds = property(get_bounds, set_bounds)

   def _depends(me):
      """enumerate all parameters the bounds depend on."""
      def check(x): return isinstance(x, param)
      for b in me._bexp:
         if check(b): yield b
         elif isinstance(b, parex):
            for c in b.preorder(check):
               yield c

   def update(me): #bounds
      lo, hi = me._bexp
      if type(lo) in (param, parex):
         lo = lo.value #no variables
      if type(hi) in (param, parex):
         hi = hi.value #no variables
      if hi is not None and lo > hi: 
         print "Bound error:",str(me)
      me.x.bounds = lo, hi

   def get_kind(me): return me.x.kind
   def set_kind(me, k): me.x.kind = k
   kind = property(get_kind, set_kind)

   status = property(lambda me: me.x.status)

   primal = property(lambda me: me.x.primal)

   dual = property(lambda me: me.x.dual)

   def get_name(me): return me.x.name
   def set_name(me, n): me.x.name=n
   name = property(get_name, set_name)

   def __repr__(me):
       c = me.x
       return "%s=%f"%(c.name, c.primal)

   def __str__(me):
       c = me.x
       return "%s=%f"%(c.name, c.primal)

   def __le__(me, b):
       if me._bad_type(b): return NotImplemented
       if isConst(b):
          me.bounds = (me._bexp[0], b)
          return me
       return constraint(None, me-b, 0)

   def __ge__(me, b): 
       if me._bad_type(b): return NotImplemented
       if isConst(b):
          me.bounds = (b, me._bexp[1])
          return me
       return constraint(0, me-b, None)

   def __eq__(me, b):
       if me._bad_type(b): return NotImplemented
       if isConst(b):
          me.bounds = (b, b)
          return me
       return constraint(0, me-b, 0)

   def bind(me, row, name):
       """bind this variable as a constraint"""
       a,b = me._bexp
       #print +me <= None # False
       con = constraint(a, +me, b)
       return con.bind(row, name)

   """
   def __del__(me):
      for p in me._depends(): 
         p.unregister(me)
      del me._bexp
      print "deleting "+me.name
   """

class objective(object):
   """An objective, which takes care of automatic update."""
   def __init__(me, expr):
       me.expr = expr
       me.relates()

   def relates(me):
       def check(x): return isinstance(x, param)
       for p in me.expr.preorder(check):
          p.register(me)

   def update(me):
       me.mod.objcoef(me.expr.linearize())

   def bind(me, mod):
       """bind the objective to a model."""
       me.mod = mod
       me.update()

   """
   def __del__(me):
       me.relates(False)
   """

class constraint(object):
   """A constraint. Such an object is 
created by a comparison (<=, >=, or ==)
between parexs."""

   def __init__(me, lo, expr, hi):
      me.lo = lo
      me.expr = expr
      me.hi = hi
      me.row = None

   def get_bounds(me): return me.row.bounds
   def set_bounds(me, b): me.row.bounds = b
   bounds = property(get_bounds, set_bounds)

   status = property(lambda me: me.row.status)

   primal = property(lambda me: me.row.primal)

   dual = property(lambda me: me.row.dual)

   def get_name(me): return me.row.name
   def set_name(me, n): me.row.name=n
   name = property(get_name, set_name)

   def relates(me):
      """register for possible changes."""
      def check(x): return isinstance(x,param)
      for p in me.expr.preorder(check):
         p.register(me)
      for b in (me.lo, me.hi):
         if check(b): b.register(me)
         elif isinstance(b, parex):
            for p in b.preorder(check):
                p.register(me)

   def vbounds(me):
       """value of bounds"""
       lo, hi = me.lo, me.hi
       if type(me.lo) in (param, parex):
          lo = me.lo.value #no variables
       if type(me.hi) in (param, parex):
          hi = me.hi.value #no variables
       return lo, hi

   def update(me): #update row (usually before solve)
       rex = me.expr.linearize()
       lo, hi = me.vbounds()
       if lo is not None: lo -= rex.const #linexp
       if hi is not None: hi -= rex.const #linexp
       me.row.bounds = lo, hi
       me.row.matrix = rex.matrix()

   def bind(me, row, name):
       """bind this constraint to a row."""
       row.name = name
       me.row = row
       me.update() #active update
       me.relates()
       return me

   def __repr__(me):
       ret = 's.t. %s: '
       if me.row: ret = ret%me.row.name
       if me.lo is not None and me.lo != me.hi: 
          ret += repr(me.lo) + " <= "
       ret += repr(me.expr)
       if me.hi is not None: 
          ret +=  " <= " if me.lo != me.hi else " == "
          ret += repr(me.hi)
       return ret

   def __str__(me):
       ret = 's.t. %s: '
       if me.row: ret = ret%me.row.name
       if me.lo is not None and me.lo != me.hi: 
          ret += str(me.lo) + " <= "
       ret += str(me.expr)
       if me.hi is not None: 
          ret +=  " <= " if me.lo != me.hi else " == "
          ret += str(me.hi)
       return ret


class parex(_dirt_):
   """expression that can take parameter objects.
When parameters change, parex sits in the middle
to have the model updated.
"""

   def __init__(me, left, op, rite):
      me.left = left
      me.op = str(op) #must be str 
      me.rite = rite
      me.constr = not (isConst(left) and isConst(rite))

   def isConst(me): return not me.constr

   @staticmethod
   def pretty_push(expr, op, nodes):
      def priority(op):
         if op in ('<=', '>=', '=='):
            return -1
         return ['+','-','*','/','ps','ng','**'].index(op)/2

      if isinstance(expr, parex):
         if priority(expr.op) < priority(op):
            nodes.append(')')
            nodes.append(expr)
            nodes.append('(')
         else: nodes.append(expr)
      else: nodes.append(expr)

   def pinorder(me):
      """pretty inorder traversal for print."""
      nodes = [me] #for tree traversion
      while len(nodes)>0:
         cur = nodes.pop() #explore
         if not isinstance(cur, parex):
            yield cur; continue
         me.pretty_push(cur.rite, cur.op, nodes)
         nodes.append(cur.op)
         if cur.op in ('ps','ng'): continue
         me.pretty_push(cur.left, cur.op, nodes)

   def __repr__(me):
      ret = ""
      for i in me.pinorder():
         if type(i) in (param, variable):
            ret += i.name
         elif i in ('ps', 'ng'): 
            ret += {'ps':'+','ng':'-'}[i]
         elif type(i) is str:
            ret += i
         else: ret += repr(i)
      return ret

   def __str__(me):
      cols = {}
      def check(x): return isinstance(x, variable)
      for v in me.preorder(check): 
         cols[v.x.index]=v.x
      lexp = me.linearize()
      return lexp.tostr(cols)

   def preorder(me, check=lambda x:True):
      """reversed preorder traversal."""
      nodes = [me] #for tree traversion
      while len(nodes)>0:
         cur = nodes.pop() #explore
         if not isinstance(cur, parex):
            if check(cur): yield cur
            continue
         nodes.append(cur.op)
         nodes.append(cur.left)
         nodes.append(cur.rite)

   def linearize(me, const=None): 
       """
convert this expression to a linexp.
returns a linexp or a number.
"""
       stack = []
       for t in me.preorder():
          tt = type(t)
          if tt in (int, float, long):
             stack.append(t)
          elif isinstance(t, param):
             stack.append(t.value)
          elif isinstance(t, variable):
             if const: raise Exception,\
                   "Not a constant!"
             stack.append(linexp(t)\
               if const is None else t.primal)
          else: stack.append({ #switch(t) 
            '+': lambda a,b: a+b,
            '-': lambda a,b: a-b,
            '*': lambda a,b: a*b,
            '/': lambda a,b: (a+0.0)/b,
            '**': lambda a,b: a**b,
            '<=': lambda a,b: a<=b,
            '>=': lambda a,b: a>=b,
            '==': lambda a,b: a==b,
            'ps': lambda a,b: +b,
            'ng': lambda a,b: -b
          }[t](stack.pop(), stack.pop()))
       assert len(stack)==1
       return stack[0]


   def evaluate(me): 
       """
evaluate this expression to a number with
variables taking their primal values.
"""
       return me.linearize(False)

   #the value when the parex is a constant 
   value = property(lambda me: me.linearize(True))

   def __le__(me, b): #me <= b
       """
   when you have something like this:
     rex = (expr1 <= expr2 <= expr3)
   the rex gets 'expr2 <= expre3',
   and the constraint 'expr1 <= expr2' is lost
   (when expr1 or expr3 contains variables, 
    the constraint is not well defined).
   However, if expr1 and expr3 are CONSTANTS,
   such as: 0 <= expr <= 3, then nothing is lost.
   'expr' must be an parex that is not a constant."""
       if me._bad_type(b): return NotImplemented
       if isConst(me) and isConst(b):
          return parex(me, "<=", b)
       if not isConst(me) and not isConst(b):
          return constraint(None, me-b, 0)
       if not isConst(me): 
          if me.constr is True:
             me.constr = constraint(None, me, b)
          else: #had been compared before
             if me.constr.hi: # a >= me <= b
               print "WARNING: overriding hi"
             me.constr.hi = b
          return me.constr
       if isinstance(b, variable):
          return constraint(0, b - me, None)
       if b.constr is True:
             b.constr = constraint(me, b, None)
       else: #had been compared before
             b.constr.lo = me
       return b.constr


   def __ge__(me, b): # me >= b
       if me._bad_type(b): return NotImplemented
       if isConst(me) and isConst(b):
          return parex(me, ">=", b)
       if not isConst(me) and not isConst(b):
          return constraint(0, me-b, None)
       if not isConst(me): 
          if me.constr is True:
             me.constr = constraint(b, me, None)
          else: #had been compared before
             if me.constr.lo: # a <= me >= b
               print "WARNING: overriding lo"
             me.constr.lo = b
          return me.constr
       if isinstance(b, variable):
          return constraint(None, b-me, 0)
       if b.constr is True:
             b.constr = constraint(None, b, me)
       else: #had been compared before
             b.constr.hi = me
       return b.constr

   def __eq__(me, b):
       if me._bad_type(b): return NotImplemented
       if isConst(me) and isConst(b):
          return parex(me, "==", b)
       if isConst(me): return constraint(me, b, me)
       if isConst(b): return constraint(b, me, b)
       if me.constr is not True:
          #possibly: expr <= me == b
          print "WARNING: discarding constraint."
       return constraint(0, me-b, 0)


class linexp(object): #linear expressions
   """class linexp for pymprog.
   this class facilitates constraints evaluation.
   """

   def __init__(me, var=None, coef=1.0):
       me.const = 0
       me.mat = []
       if var!=None: 
          me.mat.append((var.x.index,coef))

   def matrix(me): #get the corresponding matrix row
       return me.mat

   def transmat(me, u):
      u.const= me.const
      u.mat = me.mat[:]

   def tostr(me, cols):
       ret, s = '', ''
       for i,cf in me.mat:
           cf = s if cf==1 else '- ' if cf==-1 else\
              "%s%g "%(s,cf) if cf>=0 else "%g "%cf
           ret += "%s%s"%(cf, cols[i].name)
           s = '+ ' # after first item, use '+'
       if me.const < 0: ret += str(me.const)
       if me.const > 0: ret += '+' + str(me.const)
       return ret

   def _bad_type(me, b):
       return type(b) not in (int, float, long, linexp)

   #If one of those methods does not support the operation with 
   #the supplied arguments, it should return NotImplemented.
   def __add__(me, b):
       if me._bad_type(b): return NotImplemented
       rex = linexp()
       me.transmat(rex)
       if type(b) in (int, long, float):
          rex.const += b
          return rex
       #assert type(b) == linexp:
       rex.const += b.const
       j = 0      
       for i,v in b.mat:
          while j<=len(rex.mat):
             if j==len(rex.mat):
                rex.mat.append((i,v))
                break
             vid, cf = rex.mat[j]
             if vid == i:
                rex.mat[j] = (i, cf+v)
                j += 1
                break
             if vid > i:
                rex.mat.insert(j,(i,v))
                j += 1
                break
             j += 1 # vid < i
       return rex

   def __radd__(me, b):
       if me._bad_type(b): return NotImplemented
       return me + b

   def __mul__(me, b):
       if type(b) not in (int, float):
          return NotImplemented
       rex = linexp()
       rex.const = me.const*b
       rex.mat = [(i,c*b) for i,c in me.mat]
       return rex

   def __rmul__(me, b):
       if type(b) not in (int, float):
          return NotImplemented
       return me * b

   def __sub__(me, b):
       if me._bad_type(b): return NotImplemented
       return me + b*(-1.0)

   def __rsub__(me, b): # b - me
       if me._bad_type(b): return NotImplemented
       return me*(-1.0) + b

   def __div__(me, b):
       if type(b) not in (int, long, float):
          return NotImplemented
       return me * (1.0/b)

   def __pos__(me): 
       return me 

   def __neg__(me):
       return me*(-1.0)

_good_types = (
     int, float, long, type(None),
     variable, param, parex)
