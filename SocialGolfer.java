import java.util.*;
import java.io.*;
import com.hexaly.optimizer.*;

public class SocialGolfer {
    // Number of groups
    private int nbGroups;
    // Size of each group
    private int groupSize;
    // Number of week
    private int nbWeeks;
    // Number of golfers
    private int nbGolfers;

    // Objective
    private HxExpression obj;

    // Hexaly Optimizer.
    private final HexalyOptimizer optimizer;

    // Decisions variables
    private HxExpression[][][] x;

    private SocialGolfer(HexalyOptimizer optimizer) {
        this.optimizer = optimizer;
    }

    // Read instance data
    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            nbGroups = input.nextInt();
            groupSize = input.nextInt();
            nbWeeks = input.nextInt();
        }
        nbGolfers = nbGroups * groupSize;
    }

    private void solve(int limit) {
        // Declare the optimization model
        HxModel model = optimizer.getModel();

        x = new HxExpression[nbWeeks][nbGroups][nbGolfers];

        // Decision variables
        // 0-1 decisions variables: x[w][gr][gf]=1 if golfer gf is in group gr on week w
        for (int w = 0; w < nbWeeks; ++w) {
            for (int gr = 0; gr < nbGroups; ++gr) {
                for (int gf = 0; gf < nbGolfers; ++gf) {
                    x[w][gr][gf] = model.boolVar();
                }
            }
        }

        // Each week, each golfer is assigned to exactly one group
        for (int w = 0; w < nbWeeks; ++w) {
            for (int gf = 0; gf < nbGolfers; ++gf) {
                HxExpression nbGroupsAssigned = model.sum();
                for (int gr = 0; gr < nbGroups; ++gr) {
                    nbGroupsAssigned.addOperand(x[w][gr][gf]);
                }
                model.constraint(model.eq(nbGroupsAssigned, 1));
            }
        }

        // Each week, each group contains exactly groupSize golfers
        for (int w = 0; w < nbWeeks; ++w) {
            for (int gr = 0; gr < nbGroups; ++gr) {
                HxExpression nbGolfersInGroup = model.sum();
                for (int gf = 0; gf < nbGolfers; ++gf) {
                    nbGolfersInGroup.addOperand(x[w][gr][gf]);
                }
                model.constraint(model.eq(nbGolfersInGroup, groupSize));
            }
        }

        // Golfers gf0 and gf1 meet in group gr on week w if both are
        // assigned to this group for week w
        HxExpression[][][][] meetings = new HxExpression[nbWeeks][nbGroups][nbGolfers][nbGolfers];
        for (int w = 0; w < nbWeeks; ++w) {
            for (int gr = 0; gr < nbGroups; ++gr) {
                for (int gf0 = 0; gf0 < nbGolfers; ++gf0) {
                    for (int gf1 = gf0 + 1; gf1 < nbGolfers; ++gf1) {
                        meetings[w][gr][gf0][gf1] = model.and(x[w][gr][gf0], x[w][gr][gf1]);
                    }
                }
            }
        }

        // The number of meetings of golfers gf0 and gf1 is the sum
        // of their meeting variables over all weeks and groups
        HxExpression[][] redundantMeetings;
        redundantMeetings = new HxExpression[nbGolfers][nbGolfers];
        for (int gf0 = 0; gf0 < nbGolfers; ++gf0) {
            for (int gf1 = gf0 + 1; gf1 < nbGolfers; ++gf1) {
                HxExpression nbMeetings = model.sum();
                for (int w = 0; w < nbWeeks; ++w) {
                    for (int gr = 0; gr < nbGroups; ++gr) {
                        nbMeetings.addOperand(meetings[w][gr][gf0][gf1]);
                    }
                }
                redundantMeetings[gf0][gf1] = model.max(model.sub(nbMeetings, 1), 0);
            }
        }

        // the goal is to minimize the number of redundant meetings
        obj = model.sum();
        for (int gf0 = 0; gf0 < nbGolfers; ++gf0) {
            for (int gf1 = gf0 + 1; gf1 < nbGolfers; ++gf1) {
                obj.addOperand(redundantMeetings[gf0][gf1]);
            }
        }
        model.minimize(obj);

        model.close();

        // Parametrize the optimizer
        optimizer.getParam().setTimeLimit(limit);

        optimizer.solve();
    }

    /* Write the solution in a file with the following format:
     *- the objective value
     * - for each week and each group, write the golfers of the group
     * (nbWeeks x nbGroupes lines of groupSize numbers). */
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println(obj.getValue());
            for (int w = 0; w < nbWeeks; ++w) {
                for (int gr = 0; gr < nbGroups; ++gr) {
                    for (int gf = 0; gf < nbGolfers; ++gf) {
                        if (x[w][gr][gf].getValue() == 1) {
                            output.print(gf + " ");
                        }
                    }
                    output.println();
                }
                output.println();
            }
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java SocialGolfer inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "10";

        try (HexalyOptimizer optimizer = new HexalyOptimizer()) {
            SocialGolfer model = new SocialGolfer(optimizer);
            model.readInstance(instanceFile);
            model.solve(Integer.parseInt(strTimeLimit));
            if (outputFile != null) {
                model.writeSolution(outputFile);
            }
        } catch (Exception ex) {
            System.err.println(ex);
            ex.printStackTrace();
            System.exit(1);
        }
    }

}
