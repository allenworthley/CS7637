# Your Agent for solving Raven's Progressive Matrices. You MUST modify this file.
#
# You may also create and submit new files in addition to modifying this file.
#
# Make sure your file retains methods with the signatures:
# def __init__(self)
# def Solve(self,problem)
#
# These methods will be necessary for the project's main method to run.

# Install Pillow and uncomment this line to access image processing.
from PIL import Image, ImageChops
import numpy as np
import csv


def score(num1, num2=None):
    if num2 is not None:
        # Average if two provided
        total = (num1 + num2)
    else:
        total = num1

    # Divide by zero catch
    if total == 0 or total < 0.00001:
        total = 0.00001

    # 3x3 fits model better with return of 1
    return 1


def two_by_two_score(num1, num2=None):
    if num2 is not None:
        # Average if two provided
        total = (num1 + num2)
    else:
        total = num1

    # Divide by zero catch
    if total == 0 or total < 0.00001:
        total = 0.00001

    return 1 / total


def add_vote(vote_dict, key_to_add, answer_num, value_to_add):
    # Expecting
    if key_to_add in vote_dict.keys():
        vote_dict[key_to_add][answer_num] = value_to_add
    else:
        vote_dict.setdefault(key_to_add, [0, 0, 0, 0, 0, 0, 0, 0])
        vote_dict[key_to_add][answer_num] = value_to_add
    pass


def operation(i, image1, image2=None):
    # ------------------- Logical ------------------- #
    # AND
    if i == 0:
        return np.array(ImageChops.logical_and(Image.fromarray(image1), Image.fromarray(image2)))
    # OR
    elif i == 1:
        return np.array(ImageChops.logical_or(Image.fromarray(image1), Image.fromarray(image2)))
    # XOR
    elif i == 2:
        return np.array(ImageChops.logical_xor(Image.fromarray(image1), Image.fromarray(image2)))

    # ------------------- Affine ------------------- #
    # Identity
    elif i == 3:
        return np.array(Image.fromarray(image1))
    # rotation 90
    elif i == 4:
        return np.array(Image.fromarray(image1).rotate(90))
    # rotation 180
    elif i == 5:
        return np.array(Image.fromarray(image1).rotate(180))
    # rotation 270
    elif i == 6:
        return np.array(Image.fromarray(image1).rotate(270))
    # flip left to right
    elif i == 7:
        return np.array(Image.fromarray(image1).transpose(method=Image.FLIP_LEFT_RIGHT))
    # flip top to bottom
    elif i == 8:
        return np.array(Image.fromarray(image1).transpose(method=Image.FLIP_TOP_BOTTOM))


def get_dpr(matrix1, matrix2):
    black_mx1 = np.count_nonzero(matrix1 == 1)
    black_mx2 = np.count_nonzero(matrix2 == 1)
    return (black_mx1 / matrix1.size) - (black_mx2 / matrix2.size)


def get_ipr(matrix1, matrix2):
    both_mx1_mx2 = np.count_nonzero(np.logical_or(matrix1, matrix2) == 1)
    mx1_black = np.count_nonzero(matrix1 == 1)
    mx2_black = np.count_nonzero(matrix2 == 1)

    if mx1_black == 0:
        mx1_black = 1
    if mx2_black == 0:
        mx2_black = 1

    return (both_mx1_mx2 / mx1_black) - (both_mx1_mx2 / mx2_black)


def tversky(given_mx1, given_mx2, a=None):
    # Assumes given matrices are np arrays of picture in True/False format
    # Equal weight for first and second matrix if a = None

    # 1 converts to numeric for quick calculations
    mx1 = given_mx1 * 1
    mx2 = given_mx2 * 1

    if a is None:
        a = 0.5
    diff = (mx1 - mx2).flatten()
    only_a = np.sum(diff == 1)
    only_b = np.sum(diff == -1)
    both_a_b = np.sum(diff == 0)

    return both_a_b / (a * only_a + (1 - a) * only_b + both_a_b)


class Agent:
    # The default constructor for your Agent. Make sure to execute any
    # processing necessary before your Agent starts solving problems here.
    #
    # Do not add any variables to this signature; they will not be used by
    # main().
    def __init__(self):
        pass

    # The primary method for solving incoming Raven's Progressive Matrices.
    # For each problem, your Agent's Solve() method will be called. At the
    # conclusion of Solve(), your Agent should return an int representing its
    # answer to the question: 1, 2, 3, 4, 5, or 6. Strings of these ints
    # are also the Names of the individual RavensFigures, obtained through
    # RavensFigure.getName(). Return a negative number to skip a problem.
    #
    # Make sure to return your answer *as an integer* at the end of Solve().
    # Returning your answer as a string may cause your program to crash.
    def Solve(self, problem):
        # Problems object is passed and has the following structure:
        #   problem.figures - dictionary of images label A, B, C and 1 through 6
        #       figures.name
        #       figures.visualFilename = image location in form 'Problems\\Basic Problems B\\Basic Problem B-01\\C.png

        # parse the problem figures for ease of use
        problem_matrix = {}
        answer_set = {}

        # Convert data and then segment
        for k, v in problem.figures.items():
            # Convert to black and white image
            img = Image.open(v.visualFilename).convert('1')
            img_array = np.array(img)
            if k in ["A", "B", "C", "D", "E", "F", "G", "H"]:
                problem_matrix.setdefault(k, img_array)
            elif k in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                answer_set.setdefault(k, img_array)

        # Used to track votes by heuristic
        vote_summary = dict()

        if "H" in problem_matrix.keys():
            # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
            #   3 x 3 Case
            # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#

            # Setup votes for answers
            votes = [0, 0, 0, 0, 0, 0, 0, 0]
            # track heuristic votes
            # Approach, Heuristic, Operation, votes for answer set 1-8

            # ------------------- Parameters for code ------------------- #
            # tversky cutoff
            ts_cutoff = 0.02
            # DPR / IPR cutoff
            ratio_cutoff = 0.01
            change_ratio_cutoff = 0.12

            # 0.02, 0.01, and 0.12 maximize fit for given problems

            ##############################################################
            #   Tversky Logical and Affine transformations
            ##############################################################

            # result structure: columns-> operation (and, or..) rows -> different tests/heuristics
            ts_result = [[], [], []]

            for i in range(0, 3):
                # ------------------- Row ------------------- #
                a_b_c = tversky(
                    operation(i, problem_matrix["A"],
                              problem_matrix["B"]),
                    problem_matrix["C"])
                d_e_f = tversky(
                    operation(i, problem_matrix["D"],
                              problem_matrix["E"]),
                    problem_matrix["F"])

                # Row Test
                if (1 - a_b_c < ts_cutoff) and (1 - d_e_f < ts_cutoff):
                    ts_result[i].append(1)
                else:
                    ts_result[i].append(0)

                # ------------------- Column ------------------- #
                a_d_g = tversky(
                    operation(i, problem_matrix["A"],
                              problem_matrix["D"]),
                    problem_matrix["G"])

                b_e_f = tversky(
                    operation(i, problem_matrix["B"],
                              problem_matrix["E"]),
                    problem_matrix["F"])

                # Col Test
                if (1 - a_d_g < ts_cutoff) and (1 - b_e_f < ts_cutoff):
                    ts_result[i].append(1)
                else:
                    ts_result[i].append(0)

                # ------------------- Left Diagonal ------------------- #
                b_f_g = tversky(
                    operation(i, problem_matrix["B"],
                              problem_matrix["F"]),
                    problem_matrix["G"])

                c_d_h = tversky(
                    operation(i, problem_matrix["C"],
                              problem_matrix["D"]),
                    problem_matrix["H"])

                # Left Diagonal Test
                if (1 - b_f_g < ts_cutoff) and (1 - c_d_h < ts_cutoff):
                    ts_result[i].append(1)
                else:
                    ts_result[i].append(0)

                # ------------------- Right Diagonal ------------------- #
                c_e_g = tversky(
                    operation(i, problem_matrix["C"],
                              problem_matrix["E"]),
                    problem_matrix["G"])

                a_f_h = tversky(
                    operation(i, problem_matrix["A"],
                              problem_matrix["F"]),
                    problem_matrix["H"])

                # Right Diagonal Test
                if (1 - c_e_g < ts_cutoff) and (1 - a_f_h < ts_cutoff):
                    ts_result[i].append(1)
                else:
                    ts_result[i].append(0)

                # ------------------- Bottom Right Cumulative Total ------------------- #
                b_d_e = tversky(
                    operation(i, problem_matrix["B"],
                              problem_matrix["D"]),
                    problem_matrix["E"])

                if 1 - b_d_e < ts_cutoff:
                    ts_result[0].append(1)

                else:
                    ts_result[0].append(0)

            ##############################################################
            #   DPR / IPR
            ##############################################################
            # Operation(0, -> zero represents logical AND operation
            # ------------------- Row ------------------- #
            # Row 1
            a_b_c_dpr = get_dpr(operation(0, problem_matrix["A"], problem_matrix["B"]),
                                problem_matrix["C"])
            a_b_c_ipr = get_ipr(operation(0, problem_matrix["A"], problem_matrix["B"]),
                                problem_matrix["C"])
            # Row 2
            d_e_f_dpr = get_dpr(operation(0, problem_matrix["D"], problem_matrix["E"]),
                                problem_matrix["F"])
            d_e_f_ipr = get_ipr(operation(0, problem_matrix["E"], problem_matrix["E"]),
                                problem_matrix["F"])
            # Row 1 / 2 Change
            row_1_2_change_dpr = a_b_c_dpr - d_e_f_dpr
            row_1_2_change_ipr = a_b_c_ipr - d_e_f_ipr

            # ------------------- Column ------------------- #
            # Column 1
            a_d_g_dpr = get_dpr(operation(0, problem_matrix["A"], problem_matrix["D"]),
                                problem_matrix["G"])
            a_d_g_ipr = get_ipr(operation(0, problem_matrix["A"], problem_matrix["D"]),
                                problem_matrix["G"])
            # Column 2
            b_e_h_dpr = get_dpr(operation(0, problem_matrix["B"], problem_matrix["E"]),
                                problem_matrix["H"])
            b_e_h_ipr = get_ipr(operation(0, problem_matrix["B"], problem_matrix["E"]),
                                problem_matrix["H"])
            # Column 1 / 2 Change
            col_1_2_change_dpr = a_d_g_dpr - b_e_h_dpr
            col_1_2_change_ipr = a_d_g_ipr - b_e_h_ipr

            # ------------------- Left Diagonal ------------------- #
            # Left Diagonal 1
            c_e_g_dpr = get_dpr(operation(0, problem_matrix["C"], problem_matrix["E"]),
                                problem_matrix["G"])
            c_e_g_ipr = get_ipr(operation(0, problem_matrix["C"], problem_matrix["E"]),
                                problem_matrix["G"])
            # Left Diagonal 2
            a_f_h_dpr = get_dpr(operation(0, problem_matrix["A"], problem_matrix["F"]),
                                problem_matrix["H"])
            a_f_h_ipr = get_ipr(operation(0, problem_matrix["A"], problem_matrix["F"]),
                                problem_matrix["H"])
            # Left Diagonal 1 / 2 Change
            left_1_2_change_dpr = c_e_g_dpr - a_f_h_dpr
            left_1_2_change_ipr = c_e_g_ipr - a_f_h_ipr

            # ------------------- Right Diagonal ------------------- #
            # Right Diagonal 1
            b_f_g_dpr = get_dpr(operation(0, problem_matrix["B"], problem_matrix["F"]),
                                problem_matrix["G"])
            b_f_g_ipr = get_ipr(operation(0, problem_matrix["B"], problem_matrix["F"]),
                                problem_matrix["G"])
            # Right Diagonal 2
            c_d_h_dpr = get_dpr(operation(0, problem_matrix["C"], problem_matrix["D"]),
                                problem_matrix["H"])
            c_d_h_ipr = get_ipr(operation(0, problem_matrix["C"], problem_matrix["D"]),
                                problem_matrix["H"])
            # Right Diagonal 1 / 2 Change
            right_1_2_change_dpr = b_f_g_dpr - c_d_h_dpr
            right_1_2_change_ipr = b_f_g_ipr - c_d_h_ipr

            ##############################################################
            #   Testing
            ##############################################################
            op_dict = {0: "And",
                       1: "Or",
                       2: "Xor",
                       3: "Ident",
                       4: "Rot90",
                       5: "Rot180",
                       6: "Rot270",
                       7: "L_R_Flip",
                       8: "T_B_Flip"
                       }

            answer_vote = 0

            for mx in answer_set.values():

                # ---------------------------------------------------------- #
                #   Tversky
                # ---------------------------------------------------------- #
                # expecting ts_result to be col x row, 3x5 in size
                for op in range(0, 3):
                    for test in range(0, len(ts_result[op]) - 1):
                        # ------------------- Compare Row to Answer Set ------------------- #
                        if test == 0:
                            if ts_result[op][test] == 1:
                                row_test = tversky(operation(op, problem_matrix["G"], problem_matrix["H"]), mx)
                                # Vote for this answer if tversky is close
                                if 1 - row_test < ts_cutoff:
                                    tally = score(1 - row_test)
                                    votes[answer_vote] += tally
                                    add_vote(vote_summary,
                                             "Tversky-" + "Row" + op_dict[op],
                                             answer_vote,
                                             tally)

                        # ------------------- Compare Column to Answer Set ------------------- #
                        elif test == 1:
                            if ts_result[op][test] == 1:
                                col_test = tversky(operation(op, problem_matrix["C"], problem_matrix["F"]), mx)
                                # Vote for this answer if tversky is close
                                if 1 - col_test < ts_cutoff:
                                    tally = score(1 - col_test)
                                    votes[answer_vote] += tally
                                    add_vote(vote_summary,
                                             "Tversky-" + "Col-" + op_dict[op],
                                             answer_vote,
                                             tally)

                        # ------------------- Compare Left Diagonal to Answer Set ------------------- #
                        elif test == 2:
                            if ts_result[op][test] == 1:
                                left_test = tversky(operation(op, problem_matrix["A"], problem_matrix["E"]), mx)
                                # Vote for this answer if tversky is close
                                if 1 - left_test < ts_cutoff:
                                    tally = score(1 - left_test)
                                    votes[answer_vote] += tally
                                    add_vote(vote_summary,
                                             "Tversky-" + "Left-" + op_dict[op],
                                             answer_vote,
                                             tally)

                        # ------------------- Compare Right Diagonal to Answer Set ------------------- #
                        elif test == 3:
                            if ts_result[op][test] == 1:
                                right_test = tversky(operation(op, problem_matrix["B"], problem_matrix["D"]),
                                                     mx)
                                # Vote for this answer if tversky is close
                                if 1 - right_test < ts_cutoff:
                                    tally = score(1 - right_test)
                                    votes[answer_vote] += tally
                                    add_vote(vote_summary,
                                             "Tversky-" + "Right-" + op_dict[op],
                                             answer_vote,
                                             tally)

                        # ------------------- Compare Cumulative Total to Answer Set ------------------- #
                        elif test == 4:
                            if ts_result[op][test] == 1:
                                cum_test = tversky(operation(op,
                                                             operation(op, problem_matrix["G"],
                                                                       problem_matrix["H"]),
                                                             operation(op, problem_matrix["C"],
                                                                       problem_matrix["F"])),
                                                   mx)
                                # Vote for this answer if tversky is close
                                # for added weight
                                if 1 - cum_test < ts_cutoff:
                                    tally = score(1 - cum_test) * 2
                                    votes[answer_vote] += tally
                                    add_vote(vote_summary,
                                             "Tversky-" + "Cum_T-" + op_dict[op],
                                             answer_vote,
                                             tally)

                # No logical operations needed heuristics
                # ------------------- 3x3 Reflection ------------------- #
                c_180_g = tversky(np.rot90(np.rot90(problem_matrix["C"])), problem_matrix["G"])
                # maintain format for processing later
                if 1 - c_180_g < ts_cutoff:
                    refl_test = tversky(problem_matrix["A"], np.rot90(np.rot90(mx)))
                    if 1 - refl_test < ts_cutoff:
                        tally = score(1 - refl_test) * 2
                        votes[answer_vote] += tally
                        add_vote(vote_summary,
                                 "Tversky-" + "Refl-" + op_dict[op],
                                 answer_vote,
                                 tally)

                # ---------------------------------------------------------- #
                #   DPR / IPR
                # ---------------------------------------------------------- #
                # ------------------- Row ------------------- #
                # Create test dpr / ipr
                test_row_dpr = get_dpr(operation(0, problem_matrix["G"], problem_matrix["H"]),
                                       mx)
                test_row_ipr = get_ipr(operation(0, problem_matrix["G"], problem_matrix["H"]),
                                       mx)
                # Single test
                if abs(test_row_dpr - a_b_c_dpr) < ratio_cutoff and abs(test_row_dpr - d_e_f_dpr) < ratio_cutoff:
                    tally = score(abs(test_row_dpr - a_b_c_dpr), abs(test_row_dpr - d_e_f_dpr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Row1_Row2-" + "DPR",
                             answer_vote,
                             tally)

                if abs(test_row_ipr - a_b_c_ipr) < ratio_cutoff and abs(test_row_ipr - d_e_f_ipr) < ratio_cutoff:
                    tally = score(abs(test_row_ipr - a_b_c_ipr), abs(test_row_ipr - d_e_f_ipr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Row1_Row2-" + "IPR",
                             answer_vote,
                             tally)

                # Across all rows
                row_2_3_change_dpr = d_e_f_dpr - test_row_dpr
                row_2_3_change_ipr = d_e_f_ipr - test_row_ipr
                if abs(row_1_2_change_dpr - row_2_3_change_dpr) < change_ratio_cutoff:
                    tally = score(abs(row_1_2_change_dpr - row_2_3_change_dpr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Agg_Row_Change-" + "DPR",
                             answer_vote,
                             tally)

                if abs(row_1_2_change_ipr - row_2_3_change_ipr) < change_ratio_cutoff:
                    tally = score(abs(row_1_2_change_ipr - row_2_3_change_ipr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Agg_Row_Change-" + "IPR",
                             answer_vote,
                             tally)

                # ------------------- Column ------------------- #
                # Create test dpr / ipr
                test_col_dpr = get_dpr(operation(0, problem_matrix["C"], problem_matrix["F"]),
                                       mx)
                test_col_ipr = get_ipr(operation(0, problem_matrix["C"], problem_matrix["F"]),
                                       mx)
                # Single test
                if abs(test_col_dpr - a_d_g_dpr) < ratio_cutoff and abs(test_col_dpr - b_e_h_dpr) < ratio_cutoff:
                    tally = score(abs(test_col_dpr - a_d_g_dpr), abs(test_col_dpr - b_e_h_dpr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Col1_Col2-" + "DPR",
                             answer_vote,
                             tally)

                if abs(test_col_ipr - a_d_g_ipr) < ratio_cutoff and abs(test_col_ipr - b_e_h_ipr) < ratio_cutoff:
                    tally = score(abs(test_col_ipr - a_d_g_ipr), abs(test_col_ipr - b_e_h_ipr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Col1_Col2-" + "IPR",
                             answer_vote,
                             tally)

                # Across all columns
                col_2_3_change_dpr = b_e_h_dpr - test_col_dpr
                col_2_3_change_ipr = b_e_h_ipr - test_col_ipr
                if abs(col_1_2_change_dpr - col_2_3_change_dpr) < change_ratio_cutoff:
                    tally = score(abs(col_1_2_change_dpr - col_2_3_change_dpr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Agg_Col_Change-" + "DPR",
                             answer_vote,
                             tally)

                if abs(col_1_2_change_ipr - col_2_3_change_ipr) < change_ratio_cutoff:
                    tally = score(abs(col_1_2_change_ipr - col_2_3_change_ipr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Agg_Col_Change-" + "IPR",
                             answer_vote,
                             tally)

                # ------------------- Left Diagonal ------------------- #
                # Create test dpr / ipr
                test_left_dpr = get_dpr(operation(0, problem_matrix["B"], problem_matrix["D"]),
                                        mx)
                test_left_ipr = get_ipr(operation(0, problem_matrix["B"], problem_matrix["D"]),
                                        mx)
                # Single test
                if abs(test_left_dpr - c_e_g_dpr) < ratio_cutoff and abs(test_left_dpr - a_f_h_dpr) < ratio_cutoff:
                    tally = score(abs(test_left_dpr - c_e_g_dpr), abs(test_left_dpr - a_f_h_dpr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Left1_Left2-" + "DPR",
                             answer_vote,
                             tally)

                if abs(test_left_ipr - c_e_g_ipr) < ratio_cutoff and abs(test_left_ipr - a_f_h_ipr) < ratio_cutoff:
                    tally = score(abs(test_left_ipr - c_e_g_ipr), abs(test_left_ipr - a_f_h_ipr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Left1_Left2-" + "IPR",
                             answer_vote,
                             tally)

                # Across all columns
                left_2_3_change_dpr = a_f_h_dpr - test_left_dpr
                left_2_3_change_ipr = a_f_h_ipr - test_left_ipr
                if abs(left_1_2_change_dpr - left_2_3_change_dpr) < change_ratio_cutoff:
                    tally = score(abs(left_1_2_change_dpr - left_2_3_change_dpr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Agg_Left_Change-" + "DPR",
                             answer_vote,
                             tally)

                if abs(left_1_2_change_ipr - left_2_3_change_ipr) < change_ratio_cutoff:
                    tally = score(abs(left_1_2_change_ipr - left_2_3_change_ipr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Agg_Left_Change-" + "IPR",
                             answer_vote,
                             tally)

                # ------------------- Right Diagonal ------------------- #
                # Create test dpr / ipr
                test_right_dpr = get_dpr(operation(0, problem_matrix["A"], problem_matrix["E"]),
                                         mx)
                test_right_ipr = get_ipr(operation(0, problem_matrix["A"], problem_matrix["E"]),
                                         mx)
                # Single test
                if abs(test_right_dpr - b_f_g_dpr) < ratio_cutoff and abs(test_right_dpr - c_d_h_dpr) < ratio_cutoff:
                    tally = score(abs(test_right_dpr - b_f_g_dpr), abs(test_right_dpr - c_d_h_dpr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Right1_Right2-" + "DPR",
                             answer_vote,
                             tally)

                if abs(test_right_ipr - b_f_g_ipr) < ratio_cutoff and abs(test_right_ipr - c_d_h_ipr) < ratio_cutoff:
                    tally = score(abs(test_right_ipr - b_f_g_ipr), abs(test_right_ipr - c_d_h_ipr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Right1_Right2-" + "IPR",
                             answer_vote,
                             tally)

                # Across all columns
                right_2_3_change_dpr = c_d_h_dpr - test_right_dpr
                right_2_3_change_ipr = c_d_h_ipr - test_right_ipr
                if abs(right_1_2_change_dpr - right_2_3_change_dpr) < change_ratio_cutoff:
                    tally = score(abs(right_1_2_change_dpr - right_2_3_change_dpr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Agg_Right_Change-" + "DPR",
                             answer_vote,
                             tally)
                if abs(right_1_2_change_ipr - right_2_3_change_ipr) < change_ratio_cutoff:
                    tally = score(abs(right_1_2_change_ipr - right_2_3_change_ipr))
                    votes[answer_vote] += tally
                    add_vote(vote_summary,
                             "Ratio-" + "Agg_Right_Change-" + "IPR",
                             answer_vote,
                             tally)

                # Increment answer to vote for counter
                answer_vote += 1

        else:
            # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
            #   2 x 2 Case
            # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#

            # get stats from adding in answer set
            votes = [0, 0, 0, 0, 0, 0, 0, 0]
            # Parameters
            # tversky
            tv_cutoff = 0.01
            # DPR / IPR
            tolerance = 0.05

            ##############################################################
            #   Tversky Logic and affine transformations
            ##############################################################
            tv_result = [[], [], [], [], [], []]
            for i in range(3, 9):
                # row
                a_to_b = tversky(operation(i, problem_matrix["A"]), problem_matrix["B"])
                if 1 - a_to_b < tv_cutoff:
                    tv_result[i - 3].append(1)
                else:
                    tv_result[i - 3].append(0)

                # column
                a_to_c = tversky(operation(i, problem_matrix["A"]), problem_matrix["C"])
                if 1 - a_to_c < tv_cutoff:
                    tv_result[i - 3].append(1)
                else:
                    tv_result[i - 3].append(0)

                # diagonal
                b_to_c = tversky(operation(i, problem_matrix["B"]), problem_matrix["C"])
                if 1 - b_to_c < tv_cutoff:
                    tv_result[i - 3].append(1)
                else:
                    tv_result[i - 3].append(0)

            ##############################################################
            #   DPR / IPR
            ##############################################################

            # Row
            a_b_dpr = get_dpr(problem_matrix["A"], problem_matrix["B"])
            a_b_ipr = get_ipr(problem_matrix["A"], problem_matrix["B"])

            # Col
            a_c_dpr = get_dpr(problem_matrix["A"], problem_matrix["C"])
            a_c_ipr = get_ipr(problem_matrix["A"], problem_matrix["C"])

            # Diagonal
            b_c_dpr = get_dpr(problem_matrix["B"], problem_matrix["C"])
            b_c_ipr = get_ipr(problem_matrix["B"], problem_matrix["C"])

            ##############################################################
            #   testing
            ##############################################################
            answer_vote = 0
            for mx in answer_set.values():

                # ---------------------------------------------------------- #
                #   Tversky
                # ---------------------------------------------------------- #
                # Affine transformations
                for op in range(3, len(tv_result) + 3):
                    for test in range(0, len(tv_result[0])):
                        # ------------------- Row ------------------- #
                        if test == 0:
                            if tv_result[op - 3][test] == 1:
                                row_test = tversky(operation(i, problem_matrix["C"]), mx)
                                if 1 - row_test < tv_cutoff:
                                    votes[answer_vote] += two_by_two_score(1 - row_test)

                        # ------------------- Column ------------------- #
                        elif test == 1:
                            if tv_result[op - 3][test] == 1:
                                col_test = tversky(operation(i, problem_matrix["B"]), mx)
                                if 1 - col_test < tv_cutoff:
                                    votes[answer_vote] += two_by_two_score(1 - col_test)

                        # ------------------- Diagonal ------------------- #
                        elif test == 2:
                            if tv_result[op - 3][test] == 1:
                                diag_test = tversky(operation(i, problem_matrix["A"]), mx)
                                if 1 - diag_test < tv_cutoff:
                                    votes[answer_vote] += two_by_two_score(1 - diag_test)

                # ------------------- Cumulative Total ------------------- #
                for i in range(0, 4):
                    b_op_c = tversky(operation(i, problem_matrix["B"], problem_matrix["C"]),
                                     mx)
                    if 1 - b_op_c < tv_cutoff:
                        votes[answer_vote] += two_by_two_score(1 - b_op_c)

                # ---------------------------------------------------------- #
                #   DPR / IPR
                # ---------------------------------------------------------- #
                # ------------------- Row ------------------- #
                test_row_dpr = get_dpr(problem_matrix["C"], mx)
                test_row_ipr = get_ipr(problem_matrix["C"], mx)
                if abs(test_row_dpr - a_b_dpr) < tolerance:
                    votes[answer_vote] += two_by_two_score(abs(test_row_dpr - a_b_dpr))
                if abs(test_row_ipr - a_b_ipr) < tolerance:
                    votes[answer_vote] += two_by_two_score(abs(test_row_ipr - a_b_ipr))

                # ------------------- Column ------------------- #
                test_col_dpr = get_dpr(problem_matrix["B"], mx)
                test_col_ipr = get_ipr(problem_matrix["B"], mx)
                if abs(test_col_dpr - a_c_dpr) < tolerance:
                    votes[answer_vote] += two_by_two_score(abs(test_col_dpr - a_c_dpr))
                if abs(test_col_ipr - a_c_ipr) < tolerance:
                    votes[answer_vote] += two_by_two_score(abs(test_col_ipr - a_c_ipr))

                # ------------------- Diagonal ------------------- #
                test_diag_dpr = get_dpr(problem_matrix["A"], mx)
                test_diag_ipr = get_ipr(problem_matrix["A"], mx)
                if abs(test_diag_dpr - b_c_dpr) < tolerance:
                    votes[answer_vote] += two_by_two_score(abs(test_diag_dpr - b_c_dpr))
                if abs(test_diag_ipr - b_c_ipr) < tolerance:
                    votes[answer_vote] += two_by_two_score(abs(test_diag_ipr - b_c_ipr))

                answer_vote += 1

        ##############################################################
        #   Report out
        ##############################################################
        # Export votes for each problem
        #with open("C:/Users/allen/PycharmProjects/CS7637_Milestone4/RPM-Project-Code/Vote_Folder/" +
        #          problem.name + ".csv", 'w') as vote_breakdown:
        #    for key in vote_summary.keys():
        #        vote_breakdown.write("%s,%s\n" % (key, vote_summary[key]))

        #with open("C:/Users/allen/PycharmProjects/CS7637_Milestone4/RPM-Project-Code/Vote_Folder/" +
        #          problem.name + " vote total.csv", 'w') as total_vote:
        #    for i in range(len(answer_set)):
        #        total_vote.write("%s," % votes[i])

        return votes.index(max(votes)) + 1