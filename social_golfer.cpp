#include "optimizer/hexalyoptimizer.h"
#include <fstream>
#include <iostream>
#include <sstream>
#include <vector>

using namespace hexaly;
using namespace std;

class SocialGolfer {
public:
    // Number of groups
    int nbGroups;
    // Size of each group
    int groupSize;
    // Number of week
    int nbWeeks;
    // Number of golfers
    int nbGolfers;

    // Objective
    HxExpression obj;

    // Hexaly Optimizer
    HexalyOptimizer optimizer;

    // Decisions variables
    vector<vector<vector<HxExpression>>> x;

    // Read instance data
    void readInstance(const string& fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        infile >> nbGroups;
        infile >> groupSize;
        infile >> nbWeeks;
        infile.close();

        nbGolfers = nbGroups * groupSize;
    }

    // Declare the optimization model
    void solve(int limit) {
        HxModel model = optimizer.getModel();

        // Decision variables
        // 0-1 decisions variables: x[w][gr][gf]=1 if golfer gf is in group gr on week w
        x.resize(nbWeeks);
        for (int w = 0; w < nbWeeks; ++w) {
            x[w].resize(nbGroups);
            for (int gr = 0; gr < nbGroups; ++gr) {
                x[w][gr].resize(nbGolfers);
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
                model.constraint(nbGroupsAssigned == 1);
            }
        }

        // Each week, each group contains exactly groupSize golfers
        for (int w = 0; w < nbWeeks; ++w) {
            for (int gr = 0; gr < nbGroups; ++gr) {
                HxExpression nbGolfersInGroup = model.sum();
                for (int gf = 0; gf < nbGolfers; ++gf) {
                    nbGolfersInGroup.addOperand(x[w][gr][gf]);
                }
                model.constraint(nbGolfersInGroup == groupSize);
            }
        }

        // Golfers gf0 and gf1 meet in group gr on week w if both are
        // assigned to this group for week w
        vector<vector<vector<vector<HxExpression>>>> meetings;
        meetings.resize(nbWeeks);
        for (int w = 0; w < nbWeeks; ++w) {
            meetings[w].resize(nbGroups);
            for (int gr = 0; gr < nbGroups; ++gr) {
                meetings[w][gr].resize(nbGolfers);
                for (int gf0 = 0; gf0 < nbGolfers; ++gf0) {
                    meetings[w][gr][gf0].resize(nbGolfers);
                    for (int gf1 = gf0 + 1; gf1 < nbGolfers; ++gf1) {
                        meetings[w][gr][gf0][gf1] = model.and_(x[w][gr][gf0], x[w][gr][gf1]);
                    }
                }
            }
        }

        // The number of meetings of golfers gf0 and gf1 is the sum of
        // their meeting variables over all weeks and groups
        vector<vector<HxExpression>> redundantMeetings;
        redundantMeetings.resize(nbGolfers);
        for (int gf0 = 0; gf0 < nbGolfers; ++gf0) {
            redundantMeetings[gf0].resize(nbGolfers);
            for (int gf1 = gf0 + 1; gf1 < nbGolfers; ++gf1) {
                HxExpression nbMeetings = model.sum();
                for (int w = 0; w < nbWeeks; ++w) {
                    for (int gr = 0; gr < nbGroups; ++gr) {
                        nbMeetings.addOperand(meetings[w][gr][gf0][gf1]);
                    }
                }
                redundantMeetings[gf0][gf1] = model.max(nbMeetings - 1, 0);
            }
        }

        // The goal is to minimize the number of redundant meetings
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
     *  - the objective value
     *  - for each week and each group, write the golfers of the group
     * (nbWeeks x nbGroupes lines of groupSize numbers). */
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());

        outfile << obj.getValue() << endl;
        for (int w = 0; w < nbWeeks; ++w) {
            for (int gr = 0; gr < nbGroups; ++gr) {
                for (int gf = 0; gf < nbGolfers; ++gf) {
                    if (x[w][gr][gf].getValue()) {
                        outfile << gf << " ";
                    }
                }
                outfile << endl;
            }
            outfile << endl;
        }
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: social_golfer inputFile [outputFile] [timeLimit]" << endl;
        return 1;
    }

    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "10";

    try {
        SocialGolfer model;
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL)
            model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}
