# Introduction

Operating systems manage an array of resources like CPU, memory, disk/block IO, and networking. Decisions regarding these resources are defines by policies that encode heuristics. These policies/heuristics are parameterized by a large number of constants or tunables that define quantities like queue sizes or wait times.

A core problem is the choice of these constants. More precisely, can one find values for these constants that lead to optimal values for metric(s) of interest. Typical examples of these metrics are performance (run times) or energy usage.

This problem can be treated as a mathematical optimization problem. Given:

* Subsystem (e.g. block IO) and parameters/tunables that control its operations

* Workload (e.g. read-heavy workloads)

* Metrics (e.g. read throughput in bytes/sec)

Task: find values of parameters that lead to optimal metric.

If one doesn't have any insight into the specifics of the workload and the subsystem, one should treat the problem as a black-box optimization problem:

Given function $f(x)$, find $\argmax f(x)$

with no other information about f (derivatives, additive structure etc.)

In this abstract setting, optimization requires evaluating $f$ for a range of $x$ values. In the tuning problem, this translates to evaluating the metric for a fixed workload for a range of tunables. Each such evaluation can be very expensive (time, $, etc.).

The broad field of Bayesian Optimization deals with solving such problems with a minimal number of evaluations of $f$. 
## Structure

* ml-perf-harness.sh: This bash script reads parameters from a config file (ml-perf-harness.conf), sets the appropritate variables in the kernel, and executes shell script (seq-disk-perf.sh) that runs the workload. The workload script is assumed to print the metric values to standard output.

* opt.py: The function run reads in tunables that are to be searched over, and runs the bayesian optimization procedure. More precisely, the objective function should take in an array of tunables, write them to ml-perf-harness.conf, execture ml-perf-harness.sh and read the metric value from standard output. This value is then used to update the Gaussian Process (GP) and the acquisition function.

## TBD

* Containerize the optimization script so multiple evaluations can be launched.

* More complex workloads that have non-trivial optima.

* Test:
** Learning additive structure
** Parallelization (synchronous or asynchronous using Thompson sampling from the fitted GP instead of an acquisition function)
** Replace acquisition function with an agent that encodes a policy that predicts an action (which point to evaluate next) based on state (last k evaluations + information from GP). We will most likely use TRPO/PPO for the first attempt.

