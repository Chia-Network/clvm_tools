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

cons
----

```
microseconds per operation
 cons_nest-128: 17.45846838358501784683 (-145.227675)
   cons_nest-1: 17.39702532456590233778 (-158.015124)
cons_nest-1024: 17.16396016461701279354 (141.669000)
```

`cons` does not appear to be more expensive for larger values than smaller ones,
which makes sense; it should just be a matter of re-linking nodes in a linked
list.

We round the cost for `cons` to be **18**.

arithmetic operators
--------------------

```
microseconds per operation
   minus_args-1: 7.70666002381582426750 (267.695252)
 minus_args-128: 8.28468849283707520215 (97.711628)
minus_args-1024: 9.93619235469865280663 (160.235268)

    plus_args-1: 7.87108335200222253292 (202.066991)
  plus_args-128: 8.22834010595632037166 (56.044029)
 plus_args-1024: 9.86485879531786657992 (-103.437355)

        minus-1: 37.07386096510491313438 (-65.164005)
      minus-128: 37.31547396924590032086 (684.850418)
     minus-1024: 44.00765301745640556419 (-311.244245)

  minus_empty-1: 18.93197768056325713815 (28.955077)

         plus-1: 37.93150987977916344107 (-311.333964)
       plus-128: 38.26785337309302548192 (-205.271679)
      plus-1024: 43.14185560444703781968 (199.036079)

   plus_empty-1: 19.70156277772337105603 (10.305666)
```

The cost of the `-args` versions represent the incremental cost for each
argument that's added.

Each argument adds a cost of **8**.

The `plus` and `minus` tests are a series of `cons` in between the operator
under being measured, so we need to subtract the cost of a cons from those
numbers, which is 18.

Also subtract the cost for the two arguments we pass in the test. 2 * 8 = 16.
Base cost for arithmetic operators is 38 - 18 - 16 = **4**

The cost associated with size of the arguments is almost negligible. Set the
cost for argument sizes to be **1** for each full 64 bytes increment of the sum
of the sizes of all inputs. This is most likelt an over-estimate of cost, but it
might make sense to somewhat discourage using very large numbers as well.

logical operators
-----------------

```
microseconds per operation
        logand-1: 40.76669600938964777015 (-1047.477836)
      logand-128: 41.33581299440475476104 (-954.123300)
     logand-1024: 46.94990956010031624146 (-936.090839)

  logand_empty-1: 20.03093978866725421994 (-50.448068)

        logior-1: 40.53078935944432004135 (-1325.213025)
      logior-128: 41.29484251398802996391 (-1065.863277)
     logior-1024: 46.68755145025400565828 (-979.559273)

  logior_empty-1: 20.19592225015326292237 (33.872837)

        logxor-1: 39.09174544986814936465 (-637.489807)
      logxor-128: 39.90062504019549294298 (-370.702696)
     logxor-1024: 46.85561617198785455685 (-2211.715989)

  logxor_empty-1: 20.36174479448491325684 (49.374915)

   logand_args-1: 8.19917999131587471595 (174.557730)
 logand_args-128: 8.43690526986202193882 (65.275583)
logand_args-1024: 9.71121785294736028504 (258.559719)

   logior_args-1: 8.05776795949301138933 (138.410159)
 logior_args-128: 8.28309428297639271932 (62.012846)
logior_args-1024: 9.68766435800342406992 (2.225991)

   logxor_args-1: 7.99445790224378782796 (109.249234)
 logxor_args-128: 8.18429683422132114856 (153.156509)
logxor_args-1024: 9.86714348579593725219 (119.257656)
```

Each argument adds a cost of **8**.

Subtract the cost of each `cons` in the test. Subtract 2 * 8 for the two arguments.
Base cost: 40 - 18 - 16 = **6**

The cost associated with size of the arguments is almost negligible. Set the
cost for argument sizes to be **1** for each full 64 bytes increment of the sum
of the sizes of all inputs.

```
microseconds per operation
   lognot_nest-1: 11.09480216356289083990 (93.506361)
 lognot_nest-128: 11.56139576022497195140 (72.443855)
lognot_nest-1024: 13.64894704118269963544 (358.859445)
```

The cost for `lognot` is **11**

Cost per byte is about 0.002494282107051, or 400 bytes. Round it up to 512 bytes to make the computation cheap.

comparisons
-----------

```
microseconds per operation
   grs-1: 34.06622346949757940138 (214.032501)
 grs-128: 33.86813563077357258635 (13.310709)
grs-1024: 34.17726203428513542804 (-13.402394)

    eq-1: 32.78773842104324387492 (-533.242146)
  eq-128: 32.35068700118123530274 (-47.292988)
 eq-1024: 33.03308580390728366183 (-468.884188)

    gr-1: 37.26866817978020662849 (119.402356)
  gr-128: 37.64332445395475446048 (-1421.974838)
 gr-1024: 39.90684236531975415119 (-176.440372)
```

Subtract the cost of the `cons` (18).

Base cost for `=` and `>s` is 34 - 18 = **16**.

Base cost for '>' is 37 - 18 = **19**.

The cost associated with size of the arguments is almost negligible. Set the
cost for argument sizes to be **1** for each full 64 bytes increment of the sum
of the sizes of all inputs.

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
```

We subtract the cost of the `cons` as well as the cost of the one argument
passed to the call. The base cost of a `sha256` call is 29 - 18 - 8 = **3**.

This is validated by the empty test case, where we don't pass in any arguments, 21 - 18 = 3.

Each argument adds **8** to the cost.

Looking at the `_args` tests, the sizes of the arguments contribute
approximately (10.7 - 7.51) / 1024 = 0.003115234375 per byte, or 0.199375 per 64
bytes. The cons-based test suggests (32.5 - 28.55) / 1024 = 0.00392578125 per byte, or 0.25125 per 64 bytes.

We round this up to a cost of **1** per 64 bytes.

point_add
---------

```
microseconds per operation
point_add_args-48: 358.81633385438993855132 (7337.012258)
point_add_nest-48: 928.66618174578195521462 (6944.871940)
```

`point_add` is simple in that it always take a fixed size argument (48 bytes)
and always returns a result of the same size. So, bytes of input is not a
dimention to consider.

Each argument cost **358**.

The `_nest` test has two arguments per call, so the base cost is 929 - 258 * 2 = **213**

pubkey_for_exp
--------------

```
microseconds per operation
   pubkey-1: 411.87429357178342570478 (13693.238144)
 pubkey-128: 596.85854191464670748246 (9705.620405)
pubkey-1024: 605.22852709798144132947 (6447.888774)
```

`pubkey_for_exp` takes exactly one argument, so the number of arguments is not a
dimention for computing cost.

Cost per byte is though, which comes out to (605 - 412) / 1024 = 0.1884765625 per byte, or 0.75390625 every 4 bytes.
The cost of argument size is **1** every 4 bytes.

We subtract the cost of `cons` for the base cost, which is 412 - 18 = **394**

shift
-----

```
microseconds per operation
   lsh_nest-1: 20.84560466136488088296 (433.354499)
 lsh_nest-128: 20.79416017067673294605 (1126.572455)
lsh_nest-1024: 25.46730510247955692193 (307.245374)
   ash_nest-1: 21.37283335770500514172 (-508.587091)
 ash_nest-128: 20.95820238242539090834 (416.120042)
ash_nest-1024: 24.93772379763256097363 (-630.969669)
```

base cost is **21**

cost per byte is approximately (25.4673 - 20.79416) / 1024 = 0.004563618097464,
which is roughly 1 for every 219 bytes. Let's round that up to 256 to make the
computation sheap.


divmod
------

```
microseconds per operation
   divmod-1: 46.91265776390445552124 (-2784.632849)
 divmod-128: 47.82203718888671772902 (-2413.895216)
divmod-1024: 53.72995202625930488693 (-3150.413950)
```

Subtract the cost of `cons`. The base cost for `divmod` is 47 - 18 = **29**.

The size of the parameters affect the cost approximately (53.7 - 46.9) / 1024 = 0.006640625 cost per byte, or about 0.85 per 128 bytes.
Since there are two parameters, the 1024 argument size calls have a total of 2048 bytes of input.

Add to the base cost 1 for every 64 bytes of input.

boolean
-------

```
microseconds per operation
   any_nest-1: 16.64402128398390345865 (42.087006)
 any_nest-128: 16.66299917183092205164 (25.607417)
any_nest-1024: 16.83109630988346694380 (-163.653624)
   any_args-1: 7.38027077096926653610 (-48.576435)
 any_args-128: 7.18624925873563658030 (153.813996)
any_args-1024: 7.46357063335215453748 (-19.754557)

   all_nest-1: 17.26868079992011573154 (-254.094925)
 all_nest-128: 16.89556850548427746617 (27.661935)
all_nest-1024: 16.89577726494384180000 (93.075785)

   all_args-1: 7.40318679945555135902 (104.782596)
 all_args-128: 7.33438742623401118692 (133.627395)
all_args-1024: 7.45231073885721517769 (171.902488)

   not_nest-1: 8.74373737430313902053 (204.707895)
 not_nest-128: 8.75966059863641532957 (316.316878)
not_nest-1024: 8.95408525230759977376 (33.354764)
```

Cost for `not` is **9**.

`any` and `all` appear to have the same cost, which makes sense.

The cost for each argument to `any` and `all` is: **8**

In the `any_nest` and `all_nest` we pass in two arguments.

Base cost for `any` and `all` is 17 - 8 - 8 = **1**

concat
------

```
   concat_args-1: 7.64615465062680055297 (22.534513)
 concat_args-128: 7.60789686322413771791 (96.428045)
concat_args-1024: 8.27378708463598577794 (-54.367463)

        concat-1: 38.69608616309729853810 (-1152.765079)
      concat-128: 38.26487073123671933672 (-552.257291)
     concat-1024: 40.73317496302011875287 (-943.963686)
```

`concat_args-1` et. al. measure the incremental cost of adding one more argument
to `concat`. The minimum cost is **8** per argument.

`concat-1` et. al. measured the cost of concatenating two strings of the given
size (1, 128 and 1024 respectively). When ubtracting the cost of `cons` and the
per-argument cost we have a base cost of 38 - 18 - 8 - 8 = **4**.

The cost per byte is (40.7331 - 38.2648) / (1024 + 1024) = 0.00120522.
This works out to about a cost of 1 every 830 byte.


lookups
-------

```
  lookup-2: 0.75264127646481071565 (84.744583)
lookup_2-2: 16.07882064056106941052 (188.565350)
```

`lookup-2` measures the incremental cost of making a lookup of one level deeper
in the tree. i.e. a "leg". This is close enough to **1** per leg in the path
lookup.

`lookup_2-2` measures the time it takes to perform a lookup of depth 1. This
determines the minimum overhead of this operator. Given that this is *less* than
what we've measeired for the `const` operations to string them together, it
seems reasonable to model the minimum cost for a path lookup to be 0, and just
incur a cost of **1** per leg.

Looking up the root of the environment ('1') counts as a single leg.

strlen
------

```
microseconds per operation
   strlen-1: 35.92748930799407958148 (-683.209240)
 strlen-128: 36.24953132034212188728 (-901.444649)
strlen-1024: 36.24465319313137001700 (-1030.285730)
```

base cost is 36 - 18: **18**
cost per byte is (36.245 - 35.927) / 1024 = 0.00030973

That works out to about 1 every 3228 byte, if we round that to 4096, the cost
computation is cheaper.

listp
-----

```
listp-1: 23.28633488040346577463 (183.272626)
```

Subtracting the cost of `cons`, the cost of `listp` is 23 - 18: **5**

first
-----

```
      first-1: 26.10817583474324621307 (-207.954529)
first_empty-1: 17.13094403204565097099 (146.471635)
```

The `first_empty` test is essentially just measureing the cost of `cons`, to
combine the operations. This is the overhead not related to the `first`
operation.

The cost of `first` is 26 - 18 = **8** (we use 18 to be consistent with the benchmark of just `cons`).

rest
----

```
 rest-1: 27.98314466980415460284 (-243.257210)
```

Subtracting the cost of `cons` make the cost of `rest` be 28 - 18 = **20**.

if
--

```
if-1: 39.12372429326195799604 (112.467267)
```

Subtracting the cost of `cons` make the cost of `if` be 39 - 18 = **31**.

multiplication
--------------

Multiplication is a bit complicated because you a test with an arbitrary number
of arguments would (eventually) make the resulting product "explode", and the
size would dominate the cost. Instead, to assess the cost of additional
arguments, the regular `cons`-list approach is made with pairs of operands being
multiplied.

This tests the cost of just invoking the multiplication operator, with no arguments.

```
mul_empty-1: 20.67444364641485776701 (-148.958821)
```

Base cost: 20 - 18 = **2**

These tests multiply an increasing number of pairs, of varying sized operands.
Note that each pair of operands that are multiplied are independent, the product
doesn't grow as the number of operations grow. So these functions are also
linear (making the linear regression analysis correct). The varying size operand
indicates how the cost of one multiplication grows proportionally to the size of
the operand. This growth is not linear.


```
   mul-1: 38.36149494949496130403 (-300.941172)
  mul-25: 40.64905050505050354559 (-1644.516283)
  mul-50: 38.64941414141413389416 (-309.407919)
 mul-100: 41.08951515151514399804 (-1345.524485)
 mul-200: 46.12482828282826829991 (-3188.467838)
 mul-300: 46.32987878787880475784 (195.103879)
 mul-400: 53.20610101010100123631 (-656.248566)
 mul-500: 59.86872727272729122205 (-1313.719273)
 mul-600: 66.54438383838383685998 (-2153.906949)
 mul-700: 68.45020202020204180826 (1413.826869)
 mul-800: 77.40993939393938205740 (-1818.838061)
 mul-900: 88.50753535353537415631 (-1161.687798)
mul-1000: 97.27844444444444604869 (-1372.356889)
mul-1100: 99.84733333333332438997 (-397.494667)
mul-1200: 109.63307070707070067783 (-690.611596)
mul-1300: 114.41014141414146365605 (3582.888808)
mul-1400: 128.11618181818187167664 (-2854.977818)
```

Fitting this to a quadratic curve results in:

```
A + Bx + Cx^2

A   37.7677457
B   0.0325947631
C   0.000022426822
```

We can use this formula like this:
Where `sizeof(lhs)` is the number of bytes of left-hand-side operand, and
`sizeof(rhs)` is the number of bytes of right-hand-side operand.

```
A + (sizeof(lhs) + sizeof(rhs)) * B / 2 + (sizeof(lhs) * sizeof(rhs)) * C
```

Since `A` includes the cost of `cons` and the base cost, we need to subtract
that. Meaning a cost of **18** for each multiplication (e.g. `*` with 3
operands is 2 multiplications).

The cost per argument is 1 for each 61.35955 bytes of input (the sum
of the operand sizes). Let's round this to 64 to stay consistent with most other
operations. The cost per multiplication based on operand size is:

```
(sizeof(lhs) + sizeof(rhs)) / 64 + (sizeof(lhs) * sizeof(rhs)) / 44500
```

This next test is multiplying a long series of ones with values of various sizes.
This indicates the minimum overhead for each argument. This is roughly
consistent with a base cost of **18** for each multiplication.

```
   mul_nest1-1: 19.80149494949495547758 (-100.621172)
  mul_nest1-25: 20.43567676767677809835 (-164.834990)
  mul_nest1-50: 20.99220202020201497817 (-586.657131)
 mul_nest1-100: 20.35705050505050550669 (162.667717)
 mul_nest1-200: 21.30894949494949486279 (-616.599717)
 mul_nest1-400: 22.05668686868686378943 (-738.440646)
 mul_nest1-600: 23.24113131313130864442 (42.190465)
 mul_nest1-800: 21.92672727272728039338 (784.364727)
mul_nest1-1000: 23.69393939393939874094 (-407.406061)
```

To validate this formula test a few examples:

```
2 + 18 + (1400 + 1400) / 64 + (1400 * 1400) / 44500 = 20 + 43 + 44 = 107 (measured as 110)
2 + 18 + (600 + 600) / 64 + (600 * 600) / 44500 = 20 + 18 + 8 = 46 (measured as 49)
2 + 18 + (25 + 25) / 64 + (25 * 25) / 44500 = 20 + 0 + 0 = 20 (measured as 22)
```

The under-estimate is caused by the rounding of 61 -> 64. I think that's still
worth doing to avoid a division and for consistency.
