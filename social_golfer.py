import sys
import os

# Redirect stdout and stderr to a log file in append mode
log_file = open('console.log', 'a')
sys.stdout = log_file
sys.stderr = log_file

# Add the parent directory of hexaly to the path
sys.path.append(r'C:\hexaly_13_0\bin\python')

# Print the contents of the hexaly directory to verify
print("Directory contents:", os.listdir(r'C:\hexaly_13_0\bin\python\hexaly'))

# Try importing the module
import hexaly.optimizer

# Set the environment variable for the license file
os.environ['HX_LICENSE_FILE'] = r'C:\hexaly_13_0\license.dat'

if len(sys.argv) < 2:
    print("Usage: python social_golfer.py inputFile [outputFile] [timeLimit]")
    sys.exit(1)

# Log the input file being processed
print(f"Processing input file: {sys.argv[1]}")

def read_integers(filename):
    with open(filename) as f:
        return [int(elem) for elem in f.read().split()]

def validate_result(solution_file, nb_weeks, nb_groups, nb_golfers, group_size):
    with open(solution_file, 'r') as f:
        lines = f.readlines()

    table = {}
    for week in range(1, nb_weeks + 1):
        table[week] = {}
        for group in range(1, nb_groups + 1):
            table[week][group] = []

    line_index = 1
    for week in range(1, nb_weeks + 1):
        for group in range(1, nb_groups + 1):
            players = list(map(int, lines[line_index].strip().split()))
            table[week][group] = players
            line_index += 1
        line_index += 1

    # Check part 1: Each player plays exactly once per week
    for week in range(1, nb_weeks + 1):
        has_played = [0 for _ in range(nb_golfers)]
        for group in range(1, nb_groups + 1):
            for player in table[week][group]:
                if has_played[player] == 1:
                    return False
                has_played[player] = 1

    # Check part 2: Each group contains exactly group_size players
    for week in range(1, nb_weeks + 1):
        for group in range(1, nb_groups + 1):
            if len(table[week][group]) != group_size:
                return False

    # Check part 3: No two players meet more than once
    play_together = [[0 for _ in range(nb_golfers)] for _ in range(nb_golfers)]
    for week in range(1, nb_weeks + 1):
        for group in range(1, nb_groups + 1):
            for id1 in range(group_size):
                x = table[week][group][id1]
                for id2 in range(id1 + 1, group_size):
                    y = table[week][group][id2]
                    if play_together[x][y] == 1:
                        return False
                    play_together[x][y] = 1
    return True

with hexaly.optimizer.HexalyOptimizer() as optimizer:
    #
    # Read instance data
    #
    file_it = iter(read_integers(sys.argv[1]))
    nb_groups = next(file_it)
    group_size = next(file_it)
    nb_weeks = next(file_it)
    nb_golfers = nb_groups * group_size

    #
    # Declare the optimization model
    #
    model = optimizer.model

    # Decision variables
    # 0-1 decisions variables: x[w][gr][gf]=1 if golfer gf is in group gr on week w
    x = [[[model.bool() for gf in range(nb_golfers)]
          for gr in range(nb_groups)] for w in range(nb_weeks)]

    # Each week, each golfer is assigned to exactly one group
    for w in range(nb_weeks):
        for gf in range(nb_golfers):
            model.constraint(
                model.eq(model.sum(x[w][gr][gf] for gr in range(nb_groups)), 1))

    # Each week, each group contains exactly group_size golfers
    for w in range(nb_weeks):
        for gr in range(nb_groups):
            model.constraint(
                model.eq(model.sum(x[w][gr][gf] for gf in range(nb_golfers)), group_size))

    # Golfers gf0 and gf1 meet in group gr on week w if both are
    # assigned to this group for week w
    meetings = [None] * nb_weeks
    for w in range(nb_weeks):
        meetings[w] = [None] * nb_groups
        for gr in range(nb_groups):
            meetings[w][gr] = [None] * nb_golfers
            for gf0 in range(nb_golfers):
                meetings[w][gr][gf0] = [None] * nb_golfers
                for gf1 in range(gf0 + 1, nb_golfers):
                    meetings[w][gr][gf0][gf1] = model.and_(x[w][gr][gf0], x[w][gr][gf1])

    # The number of meetings of golfers gf0 and gf1 is the sum
    # of their meeting variables over all weeks and groups
    redundant_meetings = [None] * nb_golfers
    for gf0 in range(nb_golfers):
        redundant_meetings[gf0] = [None] * nb_golfers
        for gf1 in range(gf0 + 1, nb_golfers):
            nb_meetings = model.sum(meetings[w][gr][gf0][gf1] for w in range(nb_weeks)
                                    for gr in range(nb_groups))
            redundant_meetings[gf0][gf1] = model.max(nb_meetings - 1, 0)

    # the goal is to minimize the number of redundant meetings
    obj = model.sum(redundant_meetings[gf0][gf1] for gf0 in range(nb_golfers)
                    for gf1 in range(gf0 + 1, nb_golfers))
    model.minimize(obj)

    model.close()

    # Parameterize the optimizer
    optimizer.param.nb_threads = 1
    if len(sys.argv) >= 4:
        optimizer.param.time_limit = int(sys.argv[3])
    else:
        optimizer.param.time_limit = 10

    optimizer.solve()

    #
    # Write the solution in a file with the following format:
    # - the objective value
    # - for each week and each group, write the golfers of the group
    # (nb_weeks x nbGroupes lines of group_size numbers).
    #
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w') as f:
            f.write("%d\n" % obj.value)
            for w in range(nb_weeks):
                for gr in range(nb_groups):
                    for gf in range(nb_golfers):
                        if x[w][gr][gf].value:
                            f.write("%d " % (gf))
                    f.write("\n")
                f.write("\n")

        # Validate the result
        validation_result = validate_result(sys.argv[2], nb_weeks, nb_groups, nb_golfers, group_size)
        if validation_result:
            print("The solution is valid.")
        else:
            print("The solution is invalid.")

        # Write validation result to .out file
        with open(sys.argv[2] + '.check', 'w') as out_file:
            out_file.write("valid\n" if validation_result else "invalid\n")

# Close the log file
log_file.close()