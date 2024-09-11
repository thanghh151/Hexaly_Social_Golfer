using System;
using System.IO;
using Hexaly.Optimizer;

public class SocialGolfer : IDisposable
{
    // Number of groups
    int nbGroups;

    // Size of each group
    int groupSize;

    // Number of week
    int nbWeeks;

    // Number of golfers
    int nbGolfers;

    // Hexaly Optimizer
    HexalyOptimizer optimizer;

    // Objective
    HxExpression obj;

    // Decisions variables
    HxExpression[,,] x;

    public SocialGolfer()
    {
        optimizer = new HexalyOptimizer();
    }

    /* Read instance data */
    public void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            var tokens = input.ReadLine().Split(' ');
            nbGroups = int.Parse(tokens[0]);
            groupSize = int.Parse(tokens[1]);
            nbWeeks = int.Parse(tokens[2]);
        }
        nbGolfers = nbGroups * groupSize;
    }

    public void Dispose()
    {
        if (optimizer != null)
            optimizer.Dispose();
    }

    // Declare the optimization model
    public void Solve(int limit)
    {
        HxModel model = optimizer.GetModel();

        // Decision variables
        // 0-1 decisions variables: x[w,gr,gf]=1 if golfer gf is in group gr on week w
        x = new HxExpression[nbWeeks, nbGroups, nbGolfers];
        for (int w = 0; w < nbWeeks; ++w)
        {
            for (int gr = 0; gr < nbGroups; ++gr)
            {
                for (int gf = 0; gf < nbGolfers; ++gf)
                    x[w, gr, gf] = model.Bool();
            }
        }

        // Each week, each golfer is assigned to exactly one group
        for (int w = 0; w < nbWeeks; ++w)
        {
            for (int gf = 0; gf < nbGolfers; ++gf)
            {
                HxExpression nbGroupsAssigned = model.Sum();
                for (int gr = 0; gr < nbGroups; ++gr)
                    nbGroupsAssigned.AddOperand(x[w, gr, gf]);
                model.Constraint(nbGroupsAssigned == 1);
            }
        }

        // Each week, each group contains exactly groupSize golfers
        for (int w = 0; w < nbWeeks; ++w)
        {
            for (int gr = 0; gr < nbGroups; ++gr)
            {
                HxExpression nbGolfersInGroup = model.Sum();
                for (int gf = 0; gf < nbGolfers; ++gf)
                    nbGolfersInGroup.AddOperand(x[w, gr, gf]);
                model.Constraint(nbGolfersInGroup == groupSize);
            }
        }

        // Golfers gf0 and gf1 meet in group gr on week w if both are
        // assigned to this group for week w
        HxExpression[,,,] meetings = new HxExpression[nbWeeks, nbGroups, nbGolfers, nbGolfers];
        for (int w = 0; w < nbWeeks; ++w)
        {
            for (int gr = 0; gr < nbGroups; ++gr)
            {
                for (int gf0 = 0; gf0 < nbGolfers; ++gf0)
                {
                    for (int gf1 = gf0 + 1; gf1 < nbGolfers; ++gf1)
                        meetings[w, gr, gf0, gf1] = model.And(x[w, gr, gf0], x[w, gr, gf1]);
                }
            }
        }

        // The number of meetings of golfers gf0 and gf1 is the sum
        // of their meeting variables over all weeks and groups
        HxExpression[,] redundantMeetings = new HxExpression[nbGolfers, nbGolfers];
        for (int gf0 = 0; gf0 < nbGolfers; ++gf0)
        {
            for (int gf1 = gf0 + 1; gf1 < nbGolfers; ++gf1)
            {
                HxExpression nbMeetings = model.Sum();
                for (int w = 0; w < nbWeeks; ++w)
                {
                    for (int gr = 0; gr < nbGroups; ++gr)
                        nbMeetings.AddOperand(meetings[w, gr, gf0, gf1]);
                }
                redundantMeetings[gf0, gf1] = model.Max(nbMeetings - 1, 0);
            }
        }

        // The goal is to minimize the number of redundant meetings
        obj = model.Sum();
        for (int gf0 = 0; gf0 < nbGolfers; ++gf0)
        {
            for (int gf1 = gf0 + 1; gf1 < nbGolfers; ++gf1)
                obj.AddOperand(redundantMeetings[gf0, gf1]);
        }
        model.Minimize(obj);

        model.Close();

        // Parametrize the optimizer
        optimizer.GetParam().SetTimeLimit(limit);
        optimizer.Solve();
    }

    /* Write the solution in a file with the following format:
     * - the objective value
     * - for each week and each group, write the golfers of the group
     * (nbWeeks x nbGroupes lines of groupSize numbers). */
    public void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(obj.GetValue());
            for (int w = 0; w < nbWeeks; ++w)
            {
                for (int gr = 0; gr < nbGroups; ++gr)
                {
                    for (int gf = 0; gf < nbGolfers; ++gf)
                    {
                        if (x[w, gr, gf].GetValue() == 1)
                            output.Write(gf + " ");
                    }
                    output.WriteLine();
                }
                output.WriteLine();
            }
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: SocialGolfer inputFile [solFile] [timeLimit]");
            Environment.Exit(1);
        }

        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "10";

        using (SocialGolfer model = new SocialGolfer())
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}
