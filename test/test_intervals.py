import so3g
import spt3g.core as core
import numpy as np

def length_tests(iv, rows, indent_text='    '):
    for (lo, hi), len_exp, len_comp in rows:
        iv.add_interval(lo,hi)
        print(indent_text + 'add [', lo, ',', hi, ') ->', iv.array())
        assert(len(iv.array()) == len_exp)
        assert(len((-iv).array()) == len_comp)


print('Testing interface for all data types:')
for dtype in [
        so3g.IntervalsDouble,
        so3g.IntervalsInt,
        so3g.IntervalsTime,
]:
    print('    ', dtype)
    o = dtype()
    a = o.array()
    print('    ', o)
    print('    ', a, a.dtype, a.shape)


print()
print('Testing operations.')
iv = so3g.IntervalsDouble()
iv.add_interval(1., 2.)
iv.add_interval(3., 4.)
everything = (iv + ~iv)
assert(len(everything.array()) == 1)


print()
print('Testing simple interval merging:')
iv = so3g.IntervalsDouble()
length_tests(iv, [
    ((1., 2.), 1, 2),
    ((3., 4.), 2, 3),
    ((2., 3.), 1, 2)])


print()
print('Testing domain trimming:')
iv = so3g.IntervalsDouble(0., 1.)
print('   ', iv)
length_tests(iv, [
    (( 0.1,  0.2), 1, 2),
    ((-1.0,  0.0), 1, 2),
    (( 1.0,  2.0), 1, 2),
    ((-1.0,  0.1), 1, 1),
    ((-0.2,  1.1), 1, 0),
])

print()
print('Testing domain treatment on combination')
lo0, hi0 = 0., 10.
for lo1 in [-1, 5, 11]:
    for hi1 in [-1, 5, 11]:
        iv0 = so3g.IntervalsDouble(lo0, hi0)
        iv1 = so3g.IntervalsDouble(lo1, hi1)
        ivx = iv0 * iv1
        lo, hi = ivx.domain
        print('    ', iv0.domain, ' + ', iv1.domain, ' -> ',
              ivx.domain)
        assert( lo >= max(lo0, lo1) and
                (hi==lo or hi <= min(hi0, hi1)) )
        
print()
print('Testing import.')
iv0 = so3g.IntervalsDouble()\
          .add_interval(1, 2)\
          .add_interval(3, 4)


iv1 = iv0.copy()
assert(np.all(iv0.array() == iv1.array()))

iv1 = so3g.IntervalsDouble.from_array(iv0.array())
assert(np.all(iv0.array() == iv1.array()))


print()
iv1 = so3g.IntervalsDouble()\
          .add_interval(0., 1.)\
          .add_interval(2., 3.)\
          .add_interval(4., 5.)

iv2 = so3g.IntervalsDouble()\
          .add_interval(1., 2.5)

assert(len((iv1 + iv2).array()) == 2)
assert(len((iv1 * iv2).array()) == 1)
assert(len((iv1 - iv2).array()) == 2)
assert(len((iv2 - iv1).array()) == 4)


print('Sanity check on G3Time')
ti = so3g.IntervalsTime()\
    .add_interval(core.G3Time('2018-1-1T00:00:00'),
                  core.G3Time('2018-1-2T00:00:00'))
print('    ', ti)
print('    ', ti.array())
print('    ', (-ti).array())


print()
print('Map test')
tmap = so3g.MapIntervalsTime()
tmap['a'] = ti
print('    ', tmap)
print('    ', tmap['a'])

# Can we read and write them?
print()
test_filename = 'test_intervals.g3'
print('Writing to %s' % test_filename)
w = core.G3Writer(test_filename)
f = core.G3Frame()
f['map'] = tmap
f['iv'] = iv2
w.Process(f)
del w

print()
print('Reading from %s' % test_filename)
for f in core.G3File(test_filename):
    print('   ', f)
    
