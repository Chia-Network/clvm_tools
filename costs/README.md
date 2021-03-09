benchmarking operator costs
===========================

Requirements:

* gnuplot
* numpy

Basic usage:

```
python costs/generate-benchmark.py
python costs/run-benchmark.py
python costs/analyze-benchmark.py
open test-programs/*/*.png
```

`generate-benchmark.py` generate clvm programs that execute a single operator (to the
extent possible) varying number of times, operating on varying sizes of values.

The programs are stored in a `test-programs` directory.

`run-benchmark.py` executes all programs, one at a time, timing the execution by
passing `--time` to the `brun` command. The results are stored in csv files in
each operations subdirectory under `test-prorgrams`

`run-benchmark.py` also produces a `gnuplot` file and runs `gnuplot` to produce a plot of the timings.

`run-benchmark.py`, by default, will not run tests that already have a csv
results file. To run tests again anyway, pass `--force` to the program.

`analyze-benchmark.py` performs linear regression analysis of the benchmark
results and prints the slope of the lines in number of microseconds per
additional call to the given operator.

It also generates new plots for these lines.

validating results
==================

There's a script `costs/generate-random-programs.py` that generates many random
large programs. These can be used to validate that the cost functions reflect
the true run-time of executing the programs.

The programs will be stored under a `mixed-programs` directory.

Run `costs/run-validation.py` to run all programs in `mixed-programs` and
measure the cost (by passing `-c` to `brun`) and plot the correlation between
cost and run-time.

The results are stored in `mixed-programs/results.csv` and plotted to
`mixed-programs/costs.png`.

considerations
==============

linear proporion
----------------

Note that not all programs have execution time linearly proportional to the
number of times the operation is run. This is an assumption made by
`analyze-benchmark.py`, but a human must validate this by inspecting the plots.

Specifically `concat` appear to have a polynomial or exponential execution time
(for large strings).

outliers
--------

There is no logic in `analyze-benchmark.py` to filter outliers, which may
negatively affect the analysis. To mitigate this, it's possible to run the
benchmarks multiple times to collect more samples. By default `run-benchmark.py`
will skip programs that already have a csv results file, but one can pass
`--force` to run those again anyway.

nest vs. args
-------------

Some operators take an arbitrary number of arguments. The test programs measure
the difference between passing in all values into a single call (`args`) as well
as nesting calls to the operator, while still performing the same computation,
but as multiple calls to the operator (`nest`). The difference indicates the
cost of producing an output, since `nest` produces an output for each call,
whereas `args` will only produce a single output.

cons
----

Some operations cannot be nested, like `divmod` for instance. Since it returns a
list of two values. The test programs for `divmod` builds a cons list of all the
results. This means the timings for this benchmark includes the cost of the
`cons` operation. For determining the cost of `divmod`, the cost of `cons` must
be subtracted.

cost per byte
-------------

In the results below, costs per byte is generally exaggerated, compared to the
true cost in run-time. It was chosen to generally be cost of 1 per 64 bytes,
where the true run-time is at most half that, but maybe less.

The rationale is that common hardware use 64 bytes cache line sizes, and
accessing bytes within a cache line is relatively cheap and growing the working
set by a cache line size typically result in a step up in run-time.

model
=====

The model used to ascribe costs to operations breaks down to:

* creating an output value has a cost, proportional to the size of the output
* reading input parameters has a cost, proportional to the sizes of the parameters
* performing computation or test has a cost, proportional to the sizes of the  input parameters

The tests for operators that take an arbitrary number of arguments are tested in two forms:

1. adding an increasing number of arguments. e.g. `(+ (q 1) (q 2) (q 3) ...)`
2. nesting an increasing number of calls, with additional arguments. e.g. `(+ (q 1) (+ (q 2) (+ (q 3) ...)))`

The additional time (2) takes over (1) represents the cost to produce a value
and read one input. Since in (1), producing the result is amortized over all
operands, it will be negligible.

For operations that have fixed arity, there is no need to separate the cost of
producing the output from the cost of performing the operation, it's already
baked in to the total cost.

results
=======

Results are presented as the slope of the curve, in additional microseconds it
takes for one more operation.

The value in parenthesis is the constant factor for the linear regression.

cons
----

```
microseconds per operation
   cons_nest-1: 0.24570221272216288821 (86.825906)
 cons_nest-128: 0.49376842611200050248 (82.683877)
cons_nest-1024: 1.77137488389821373680 (-17.812513)
```

Even though it seems `cons` appears to be more expensive for larger values than smaller ones,
it would not be practical to implement any such checks. It's also hard to
explain why the cost of the operation itself *would* be proportinal to the atoms.
This is most likely an effect of the larger working set.

We round the cost for `cons` to be **3** (that's 0.3 microseconds).

arithmetic operators
--------------------

```
microseconds per operation
   minus_args-1: 0.31973846654718446336 (83.817943)
 minus_args-128: 0.60121062816887393954 (77.153716)
minus_args-1024: 1.66268114284967594152 (10.884404)

    plus_args-1: 0.32626185081390507436 (84.477396)
  plus_args-128: 0.60198035378039660426 (74.269407)
 plus_args-1024: 1.71421457821139644473 (-0.765078)

        minus-1: 0.98394404483104702663 (104.404603)
      minus-128: 1.87581361583539818483 (68.535223)
     minus-1024: 6.83455363586504649476 (-368.965182)

         plus-1: 0.98827048717005028244 (106.021836)
       plus-128: 1.87569917557325127611 (89.787728)
      plus-1024: 6.97936503817604947386 (-279.183538)

  minus_empty-1: 0.23578137938015000796 (92.662884)
   plus_empty-1: 0.24540126502670769892 (89.215360)
```

Plus and minus have virtually the same timings. We lump them together.

The cost of the `-args` versions represent the incremental cost for each
argument that's added.

Each argument adds a cost of **3**.

Each additional byte of argument adds about (17 - 3) / 1024 = 0.01367. That's a
cost of 1 every 73.1429 bytes. Let's round that to every 64 bytes, to add some
additional cost to bytes.

byte cost divisor: 64

The `plus` and `minus` tests are a series of `cons` in between the operator
being measured, so we need to subtract the cost of a cons from those
numbers, which is 3.

Also subtract the cost for the two arguments we pass in the test. 2 * 3 = 6.
Base cost for arithmetic operators:

* For 1 byte atoms: 10 - 3 - 6 = **1**
* For 128 byte atoms: 19 - 3 - 6 = **11**
* For 1024 byte atoms: 70 - 3 - 6 = **61**

Each operation has two operands of the given size, so bytes per cost is:

1024 * 2 / 61 = 33.5738

We round this to 32:

byte cost divisor: **32**

logical operators
-----------------

```
microseconds per operation
        logand-1: 0.97612772647059120601 (96.938439)
      logand-128: 1.95342141674206404289 (50.320563)
     logand-1024: 6.85351315617086331855 (-160.973851)

  logand_empty-1: 0.34559469614796745063 (101.045988)

        logior-1: 1.00915896876049715480 (93.439080)
      logior-128: 1.85823029661444194538 (65.144131)
     logior-1024: 7.10537013672248551899 (-454.412875)

  logior_empty-1: 0.23302526221372546478 (101.180557)

        logxor-1: 1.02269932466485280464 (104.132608)
      logxor-128: 1.84839377280681516069 (19.609041)
     logxor-1024: 6.95645995008251816216 (-369.630982)

  logxor_empty-1: 0.24601039242464781132 (92.693472)

   logand_args-1: 0.30895456023572670512 (81.070453)
 logand_args-128: 0.58150798026770478266 (75.264390)
logand_args-1024: 1.67316052528791869847 (5.841123)

   logior_args-1: 0.30360963374833821460 (85.050523)
 logior_args-128: 0.58079771963555137937 (72.782154)
logior_args-1024: 1.57666239302069444150 (17.386227)

   logxor_args-1: 0.31274152655212039686 (86.141956)
 logxor_args-128: 0.60489392827048460433 (68.953284)
logxor_args-1024: 1.71136422587087877467 (28.892076)
```

Each argument adds a cost of **3**.

Subtract the cost of each `cons` in the test. Subtract 2 * 3 for the two arguments.
Base cost for logiocal operators:

* For 1 byte atoms: 10 - 3 - 6 = **1**
* For 128 byte atoms: 20 - 3 - 6 = **11**
* For 1024 byte atoms: 69 - 3 - 6 = **60**

Each operation has two operands of the given size, so bytes per cost is:

1024 * 2 / 61 = 33.5738

Round the byte cost divisor to: **32**

```
microseconds per operation
   lognot_nest-1: 0.33156751459271383009 (83.297258)
 lognot_nest-128: 0.59859425068648386414 (100.449810)
lognot_nest-1024: 2.63077443666830124158 (-75.015860)
```

The cost for `lognot` is **3**

Byte cost divisor is 1024 / 26 = 39.38461

Round the byte cost divisor to: **32**

comparisons
-----------

```
microseconds per operation
   grs-1: 0.45407794484037322658 (93.207489)
 grs-128: 0.82278478209519312347 (69.157214)
grs-1024: 1.95542021746606797805 (13.851156)

    eq-1: 0.45391498053504031329 (78.775223)
  eq-128: 0.80948350864615226108 (77.395751)
 eq-1024: 2.34231949190749233480 (-281.994352)
'''

Subtract the cost of the `cons` (3).

Base cost for `=` and `>s` is 5 - 3 = **2**.

Byte cost divisor is 2 * 1024 / (23 - 3) = 102.4

Round byte cost divisor to: **64**

'''
microseconds per operation
    gr-1: 0.83516945526887143014 (74.295816)
  gr-128: 1.40735951664722724885 (84.664418)
 gr-1024: 3.93887591431556893795 (-141.312945)
```

Base cost for '>' is 8 - 3 = **5**.

Byte cost divisor is 2 * 1024 / (39 - 3) = 56.88

Round the byte cost divisor to: **32**

sha-256
-------

```
microseconds per operation
        sha-1: 28.55177302241918368964 (324.926931)
      sha-128: 28.49818414035497937675 (407.883062)
     sha-1024: 32.57254548179997044599 (56.155021)
   sha_args-1: 7.51462305113815443036 (-88.108982)
 sha_args-128: 7.80882158921228786141 (119.709524)
sha_args-1024: 10.79437223109812649113 (79.329517)

  sha_empty-1: 20.66984590774052676920 (-174.334628)

----------

        sha-1: 0.45975574752144754420 (93.694481)
      sha-128: 0.73532795934131278681 (78.716874)
     sha-1024: 2.16696831346474594326 (-214.288105)

   sha_args-1: 0.13460619989003208552 (87.296594)
 sha_args-128: 0.39013345085389034006 (67.252450)
sha_args-1024: 1.45560239419398107508 (-15.067240)

  sha_empty-1: 0.33212180728239903971 (91.945749)
```

We subtract the cost of the `cons` as well as the cost of the one argument
passed to the call. The base cost of a `sha256` call is 5 - 3 = **2**.

Each argument has a cost of: **1**

The cost byte divisor is 1024 / (15 - 1) = 73.142
or 1024 / (22 - 2 - 1) = 53.894

Round the byte cost divisor to: **64**

point_add
---------

```
microseconds per operation
point_add_args-48: 419.99442704336257747855 (305.677859)
point_add_nest-48: 871.58037906847948761424 (397.973413)
```

`point_add` is simple in that it always take a fixed size argument (48 bytes)
and always returns a result of the same size. So, bytes of input is not a
dimention to consider.

Each argument cost **4200**.

The `_nest` test has two arguments per call, so the base cost is 8716 - 4200 * 2 = **316**

pubkey_for_exp
--------------

```
microseconds per operation
   pubkey-1: 419.77993839203685411121 (-58.740435)
 pubkey-128: 421.72511932749455354497 (114.776200)
pubkey-1024: 431.54759660818592692522 (-334.521863)
```

`pubkey_for_exp` takes exactly one argument, so the number of arguments is not a
dimention for computing cost.

Bytes per cost is though, which comes out to 1024 / (4314 - 4197) = 8.752

Round the byte cost divisor to **8**

We subtract the cost of `cons` for the base cost, which is 4197 - 3 = **4194**

left shift
----------

```
microseconds per operation
   lsh_nest-1: 0.27668789726277653873 (104.463363)
 lsh_nest-128: 0.65141208881274570430 (252.631747)
lsh_nest-1024: 2.60921442074267684319 (124.849076)
```

base cost is **3**

Bytes per cost is approximately 1024 / (26 - 3) = 44.5217
Round the byte cost divisor to **32**

arithmetic shift
----------------

```
microseconds per operation
   ash_nest-1: 0.59698501136284110036 (411.864322)
 ash_nest-128: 1.00045495981021415055 (164.027031)
ash_nest-1024: 3.00428881374951251004 (-147.547149)
```

Base cost is **6**

Bytes per cost is 1024 / (30 - 6) = 42.6666
Round the byte cost divisor to **32**

divmod
------

```
microseconds per operation
   divmod-1: 1.36139784302127875293 (118.046061)
 divmod-128: 2.48753251149112175611 (45.124187)
divmod-1024: 7.60455035694966419157 (-135.188393)
```

Subtract the cost of `cons`. The base cost for `divmod` is 14 - 3 = **11**.

Each invocation of `divmod` has two arguments of the specified size. so the 1024
measures are really 2048 bytes worth of argumnets.

The byte cost divisor is 1024 / (76 - 14) = 16.51612
Round the byte cost divisor to: **16**

div
---

```
microseconds per operation
   div-1: 1.23291432572562209558 (89.965160)
 div-128: 2.01471640330164980526 (39.708615)
div-1024: 4.92077671146116113476 (-249.012930)
```

Subtracting the cost of `cons` makes the base cost 12 - 3 = **9**

The byte cost divisor is 1024 / (49 - 12) = 54.4324

Round the byte cost divisor to **32**

boolean
-------

```
microseconds per operation
   any_nest-1: 0.19000809713698138537 (88.530101)
 any_nest-128: 0.36562829116372502769 (82.835091)
any_nest-1024: 0.84095327897155303098 (-3.549353)

   any_args-1: 0.12183388241646632422 (90.714322)
 any_args-128: 0.29329518624528461146 (67.709513)
any_args-1024: 0.73487293155645916354 (1.633383)

   all_nest-1: 0.20387467132301573258 (85.594616)
 all_nest-128: 0.35636644062063349558 (78.282464)
all_nest-1024: 0.80775026088508694588 (25.390237)

   all_args-1: 0.12997459586446583057 (78.599377)
 all_args-128: 0.28660873212635129548 (73.899652)
all_args-1024: 0.73993089213334262144 (-5.671898)

   not_nest-1: 0.07801654840940555613 (85.100022)
 not_nest-128: 0.07997550173735153145 (81.367959)
not_nest-1024: 0.07913310585202978920 (83.876844)
```

Cost for `not` is **1**.

Base cost for `any` and `all` is **1**.

The cost for each argument to `any` and `all` is: **3**

In the `any_nest` and `all_nest` we pass in two arguments.

concat
------

```
   concat_args-1: 0.13522339785377593402 (83.131619)
 concat_args-128: 0.44348915234610125635 (48.277132)
concat_args-1024: 2.38576786019322595322 (-85.233455)

        concat-1: 0.52174484487690686585 (89.984428)
      concat-128: 1.33459560482424621775 (-18.373504)
     concat-1024: 6.69365029026818092461 (-1151.805886)
```

`concat_args-1` et. al. measure the incremental cost of adding one more argument
to `concat`. The minimum cost is **1** per argument.

`concat-1` et. al. measured the cost of concatenating two strings of the given
size (1, 128 and 1024 respectively). When subtracting the cost of `cons` and the
per-argument cost we have a base cost of 5 - 1 - 3 = **1**.

The byte cost divisor is 2 * 1024 / (67 - 5) = 33.032
Round the byte cost divisor to **32**.

lookups
-------

```
  lookup-2: 0.14757997035453823687 (65.665985)
lookup_2-2: 0.16717336352926376319 (77.882988)
```

`lookup-2` measures the incremental cost of making a lookup of one level deeper
in the tree. i.e. a "leg". This is close enough to **1** per leg in the path
lookup.

`lookup_2-2` measures the time it takes to perform a lookup of depth 1. This
determines the minimum overhead of this operator. Given that this is *less* than
what we've measured for the `cons` operations to string them together, it
seems reasonable to model the minimum cost for a path lookup to be 0, and just
incur a cost of **1** per leg.

Looking up the root of the environment ('1') counts as a single leg.

strlen
------

```
microseconds per operation
   strlen-1: 0.46363083969539892193 (83.322011)
 strlen-128: 0.69207720665016925210 (85.274372)
strlen-1024: 1.32640170143377811307 (-140.631272)
```

base cost is 5 - 3: **2**
The byte cost divisor is 1024 / (13.26 - 4.63) = 118.655
Round the byte cost divisor to **128**.

listp
-----

```
listp-1: 0.31038065066450787333 (94.644048)
```

Subtracting the cost of `cons`, the cost of `listp` turns into 0, so charge the
smallest possible cost: **1**

first
-----

```
      first-1: 26.10817583474324621307 (-207.954529)
first_empty-1: 17.13094403204565097099 (146.471635)

      first-1: 0.32143060013064828073 (76.251001)
first_empty-1: 0.29133047587311594606 (97.778027)
```

The `first_empty` test is essentially just measureing the cost of `cons`, to
combine the operations. This is the overhead not related to the `first`
operation.

The cost of `first` is 3.2 - 2 = **1** (we use 3 to be consistent with the benchmark of just `cons`).

rest
----

```
rest-1: 0.36777596799212358691 (70.401632)
```

Subtracting the cost of `cons` make the cost of `rest` be 3.7 - 3 = **1**.

if
--

```
if-1: 0.36958951307556009436 (74.675161)
```

Subtracting the cost of `cons` make the cost of `if` be 3.7 - 3 = **1**.

multiplication
--------------

Multiplication is a bit complicated because a test with an arbitrary number
of arguments would (eventually) make the resulting product "explode", and the
size would dominate the cost. Instead, to assess the cost of additional
arguments, the regular `cons`-list approach is made with pairs of operands being
multiplied.

This tests the cost of just invoking the multiplication operator, with no arguments.

```
mul_empty-1: 0.33661753909896824366 (89.131827)
```

Base cost: 3.4 - 3 = **1**

These tests multiply an increasing number of pairs, of varying sized operands.
Note that each pair of operands that are multiplied are independent, the product
doesn't grow as the number of operations grow. So these functions are also
linear (making the linear regression analysis correct). The varying size operand
indicates how the cost of one multiplication grows proportionally to the size of
the operand. This growth is not linear.


```
   mul-1: 1.14636064545158089523 (92.316037)
  mul-25: 1.70315212029002749361 (59.487461)
  mul-50: 1.88884455701491082991 (91.127064)
 mul-100: 2.40395381029566435060 (74.305654)
 mul-200: 3.71898746429636251065 (-152.759712)
 mul-300: 5.38019049274786542725 (-144.962911)
 mul-400: 7.22410307967137121921 (-382.992354)
 mul-500: 8.42744990287291884101 (-1.193929)
 mul-600: 10.85231959167802351374 (68.892027)
 mul-700: 12.81391052743008707182 (-6.534245)
 mul-800: 15.13449056668298275952 (-485.994570)
 mul-900: 17.59338681266760673338 (-358.888971)
mul-1000: 19.78098733891571470167 (-214.282335)
mul-1100: 24.56260610789641418705 (-789.602845)
mul-1200: 27.29384148555957878557 (-1087.275990)
mul-1300: 29.80849443518868469027 (-1082.983160)
mul-1400: 31.58819694703557345861 (-1153.085545)
```

Fitting this to a quadratic curve (and multiplying by 10 to turn microseconds
into cost) results in:

```
A + Bx + Cx^2

A   12.2286128
B   0.1119215961
C   0.000080925179
```

We can use this formula like this:
Where `len(lhs)` is the number of bytes of left-hand-side operand, and
`len(rhs)` is the number of bytes of right-hand-side operand.

```
A + (len(lhs) + len(rhs)) * B / 2 + (len(lhs) * len(rhs)) * C
```

Since `A` includes the cost of `cons` and the base cost, we need to subtract
that. Making it a base cost of 12 - 1 - 3 = **8** for each multiplication (e.g.
`*` with 3 operands is 2 multiplications).

The linear byte cost divisor is 2 / 0.1119215961 = 17.8696
Round the linear byte cost divisor to: **16**

The quadratic byte cost divisor is 1 / 0.000080925179 = 12357.093
Round that to **16384**

```
(len(lhs) + len(rhs)) / 16 + (len(lhs) * len(rhs)) / 16384
```

This next test is multiplying a long series of ones with values of various sizes.
This indicates the minimum overhead for each argument. This is roughly
consistent with a base cost of **8** for each multiplication.

```
   mul_nest1-1: 0.76153535353535384278 (52.804202)
  mul_nest1-25: 0.83557575757575774933 (81.001576)
  mul_nest1-50: 1.00098989898989909619 (36.161657)
 mul_nest1-100: 1.02781818181818196400 (151.089818)
 mul_nest1-200: 1.19303030303030355164 (159.123030)
 mul_nest1-400: 1.77258585858585937522 (123.163919)
 mul_nest1-600: 2.12002020202020213802 (78.832687)
 mul_nest1-800: 2.80404040404040433287 (-39.062626)
mul_nest1-1000: 3.43048484848484847021 (-50.915515)
```

To validate this formula test a few examples:

```
1 + 8 + (1400 + 1400) / 16 + (1400 * 1400) / 16384 = 9 + 200 + 119 = 328 (measured as 315)
1 + 8 + (600 + 600) / 16 + (600 * 600) / 16384 = 9 + 75 + 21 = 105 (measured as 108)
1 + 8 + (25 + 25) / 16 + (25 * 25) / 16384 = 9 + 26 + 0 = 35 (measured as 17)
```

