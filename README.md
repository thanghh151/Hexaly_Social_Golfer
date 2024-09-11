# Hexaly_Social_Golfer

## Problem

The **Social Golfer Problem** (SGP) is about scheduling golfers into groups such that they play with as many different golfers as possible across multiple weeks. Specifically, in a golf club with 32 social golfers, each golfer plays once a week in groups of 4. The challenge is to create a schedule for 10 weeks with **maximum socialization**, i.e., minimize repeated pairings of golfers.

More generally, the problem can be formulated as follows:

- Given `m` groups of `n` golfers over `p` weeks, create a schedule that maximizes socialization.
- The complexity of the problem is not fully understood.
- Some instances, like the one mentioned with 32 golfers over 10 weeks, have known solutions with no repeated pairings.

For more details, refer to [CSPLib](http://www.csplib.org) or [MathPuzzle](http://www.mathpuzzle.com).

## Data

Each data file for the problem consists of three numbers:

1. The number of groups
2. The size of the groups (number of golfers per group)
3. The number of weeks

## Program

The decision variables are binary values `x[w][gr][gf]`, where:

- `w`: the week
- `gr`: the group
- `gf`: the golfer
- `x[w][gr][gf] = 1` if golfer `gf` is in group `gr` on week `w`, otherwise `x[w][gr][gf] = 0`.

The number of meetings between each pair of golfers `gf0` and `gf1` is stored in `nbMeetings[gf0][gf1]`. The redundant meetings for a pair of golfers can be calculated as `max(0, nbMeetings[gf0][gf1] - 1)`.

## Execution

### Windows

To run the Python script on Windows:

```bash
set PYTHONPATH=%HX_HOME%\bin\python
python social_golfer.py instances\c_4_3_3.in
```

### Linux

To run the Python script on Linux:

```bash
export PYTHONPATH=/opt/hexaly_13_0/bin/python
python social_golfer.py instances/c_4_3_3.in
```
