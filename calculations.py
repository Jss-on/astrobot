from datetime import datetime
from pulp import (
    LpProblem,
    LpMinimize,
    LpVariable,
    lpSum,
    value,
    LpContinuous,
    LpInteger,
    LpStatus,
)
import math

# decrease_ratio_list = [0.2, 0.5, 0.9]


class Calculations:
    def allocate_full(self, demand_items: list, total_num_units: int) -> list:
        demands = sorted(demand_items, key=lambda x: x[-1])
        allocated = []
        for beginning_demand, weekly_bsd in demand_items:
            if max((beginning_demand - total_num_units), 0) == 0:
                total_num_units -= beginning_demand

                allocated.append(beginning_demand)
            else:
                beginning_demand -= total_num_units
                allocated.append(total_num_units)
                total_num_units = 0
        return allocated

    def calculate_Z(
        self,
        Ti_TR: list,
        Ti_LS: list,
        D_TR: list,
        u_TR: list,
        D_LS: list,
        u_LS: list,
        Z_TR: int,
        Z_LS: int,
        decrease_ratio: float,
    ):
        of_TR = 0
        of_LS = 0
        # min_Z = 0
        prev_Z = math.inf
        # for decrease_ratio in decrease_ratio_list:
        for i in range(len(Ti_TR)):
            term1_TR = math.e ** (
                math.log(decrease_ratio) * Ti_TR[i]
            )  # 1 / max((Ti_TR[i]), 1 / (10 + abs(Ti_TR[i])))
            term2_TR = max((D_TR[i] - (u_TR[i]) * (Z_TR)), 0)
            of_TR += term1_TR * term2_TR
        for i in range(len(Ti_LS)):
            term1_LS = math.e ** (
                math.log(decrease_ratio) * Ti_LS[i]
            )  # 1 / max((Ti_LS[i]), 1 / (10 + abs(Ti_LS[i])))
            term2_LS = max((D_LS[i] - (u_LS[i]) * (Z_LS)), 0)
            of_LS += term1_LS * term2_LS
        # print(of_TR + of_LS)
        # # min_Z = math.log(of_LS + of_TR)
        # if prev_Z > math.log(of_LS + of_TR):
        #     prev_Z = math.log(of_LS + of_TR)
        #     # prev_Z =

        return math.log(of_LS + of_TR)

    def split_score(
        self,
        STD_QTY: int,
        N: int,
        Ti_TR: list,
        Ti_LS: list,
        D_TR: list,
        u_TR: list,
        D_LS: list,
        u_LS: list,
        output: int,
        product_type: str,
    ):
        # Initialize the problem
        decrease_ratio_list = [0.1, 0.3, 0.5, 0.7, 0.9]
        prob = LpProblem("Minimize_of_with_constraints", LpMinimize)
        if product_type == "MAXCIM":
            STD_QTY = STD_QTY * (1.002)
        STD_QTY_TR = [STD_QTY for i in range(len(D_TR))]
        # Create the decision variables for u_TR and u_LS
        # Here, n_TR are integer decision variables representing the multiples of STD_QTY_TR
        n_TR = [
            LpVariable(f"n_TR_{i}", cat="Integer", lowBound=0) for i in range(len(D_TR))
        ]
        u_LS = [LpVariable(f"u_LS_{i}", lowBound=0) for i in range(len(D_LS))]

        # Define u_TR as multiples of STD_QTY_TR
        u_TR = [n_TR[i] * STD_QTY_TR[i] for i in range(len(STD_QTY_TR))]

        # Auxiliary variables for the max function
        w_TR = [LpVariable(f"w_TR_{i}", lowBound=0) for i in range(len(D_TR))]
        w_LS = [LpVariable(f"w_LS_{i}", lowBound=0) for i in range(len(D_LS))]

        # Adding the max function constraints
        for i in range(len(D_TR)):
            prob += w_TR[i] >= D_TR[i] - u_TR[i]
            prob += w_TR[i] >= 0

        for i in range(len(D_LS)):
            prob += w_LS[i] >= D_LS[i] - u_LS[i]
            prob += w_LS[i] >= 0

        # Supply constraint
        prob += lpSum(u_TR) + lpSum(u_LS) == N, "Supply_Constraint"

        # Defining the objective function
        # 1 / max(Ti_TR[i], 1 / (10 + abs(Ti_TR[i]))) * w_TR[i]
        # 1 / max(Ti_LS[i], 1 / (10 + abs(Ti_LS[i]))) * w_LS[i]
        prev_Z = math.inf
        for decrease_ratio in decrease_ratio_list:
            objective = lpSum(
                [
                    (math.e ** (math.log(decrease_ratio) * Ti_TR[i])) * w_TR[i]
                    for i in range(len(Ti_TR))
                ]
            ) + lpSum(
                [
                    (math.e ** (math.log(decrease_ratio) * Ti_LS[i])) * w_LS[i]
                    for i in range(len(Ti_LS))
                ]
            )

            # Set the objective
            prob.setObjective(objective)

            # Solve the problem
            prob.solve()

            if prev_Z > math.log(value(prob.objective)):
                prev_Z = math.log(value(prob.objective))
                final_decrease_ratio = decrease_ratio

                # Results
                n_TR_solution = [n_TR[i].varValue for i in range(len(n_TR))]
                u_LS_solution = [u_LS[i].varValue for i in range(len(u_LS))]

                # Calculate the actual u_TR based on the n_TR_solution and STD_QTY_TR
                u_TR_solution = [
                    n_TR_solution[i] * STD_QTY_TR[i] for i in range(len(STD_QTY_TR))
                ]
            # if prev_Z > math.log(value(prob.objective)):
            #     prev_Z = math.log(value(prob.objective))

        if output == 0:
            # print(prob.objective)
            # print(type(prob.objective))
            # print(value(prob.objective))
            print(prev_Z, final_decrease_ratio)
            return (prev_Z, final_decrease_ratio)
        elif output == 1:
            return (n_TR_solution, u_TR_solution, u_LS_solution)
