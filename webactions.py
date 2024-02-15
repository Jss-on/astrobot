from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
# from calculations import Calculations
from selenium.webdriver.support.ui import Select
# from utilities import current_work_week, parse_week_codes
from selenium.webdriver.chrome.service import Service as ChromeService
from collections import Counter
from math import ceil

import logging
import config
import time
import platform

logging.basicConfig(
    filename="session.log",
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(module)s - %(message)s",
)



class WebActions:
    """
    A class used to perform web actions using Selenium.

    This class encapsulates methods for web interactions such as navigating,
    logging in, and interacting with web elements. It is configured to use headless Chrome.

    Attributes:
        driver (webdriver.Chrome): The Chrome WebDriver instance for browser interactions.
        url (str): URL for the web application to interact with.
        username (str): Username for login.
        password (str): Password for login.
        wait (WebDriverWait): WebDriverWait instance for managing explicit waits.
        product_type (dict): Mapping of product types for use in interactions.
    """

    def __init__(self):
        """
        Initializes the WebActions with configured credentials and sets up the headless Chrome driver.

        The method sets up logging and initializes the Chrome WebDriver with the necessary options
        for running in headless mode. It also configures the credentials and URL based on the DEBUG
        setting in the config module.
        """

        if platform.system() == "Linux":
            print("Linux")
            logging.info(f"Running at {platform.system()}.")
            self.driver_location = "/usr/bin/chromedriver"
            self.binary_location = "/usr/bin/google-chrome"
            chrome_service = ChromeService(executable_path=self.driver_location)

            if config.HEADLESS:
                # Set Chrome options for headless mode
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.binary_location = self.binary_location
                # Set up the Chrome service with the path to the ChromeDriver
                chrome_service = ChromeService(executable_path=self.driver_location)
                self.driver = webdriver.Chrome(
                    service=chrome_service, options=chrome_options
                )
            else:
                self.driver = webdriver.Chrome()
        elif platform.system() == "Windows":
            print("Windows")
            logging.info(f"Running at {platform.system()}.")
            if config.HEADLESS:
                # Set Chrome options for headless mode
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                self.driver = webdriver.Chrome(options=chrome_options)
            else:
                self.driver = webdriver.Chrome()

        if config.DEBUG:
            self.url = config.DEV_CREDENTIALS["url"]
            self.username = config.DEV_CREDENTIALS["username"]
            self.password = config.DEV_CREDENTIALS["password"]
        else:
            self.url = config.PROD_CREDENTIALS["url"]
            self.username = config.PROD_CREDENTIALS["username"]
            self.password = config.PROD_CREDENTIALS["password"]

        self.wait = WebDriverWait(self.driver, 10)
        self.product_type = {
            "COMETS": "edit-producttype-C",
            "MAXCIM": "edit-producttype-M",
        }
        self.allocation_counter = 0
        logging.info(f"{self.__class__.__name__} initialized")

    def login(self):
        """
        Handles the login process on the website using configured credentials.

        Navigates to the login page, inputs credentials, and submits the login form.
        Uses WebDriverWait to ensure elements are clickable or present before interaction.

        Raises:
            TimeoutException: If an expected condition is not met during login.
        """

        logging.info(f"{self.__class__.__name__}.login method called")
        self.driver.get(self.url)

        self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "li.menu-658.first.last> a"))
        ).click()
        self.wait.until(EC.presence_of_element_located((By.ID, "edit-name"))).send_keys(
            self.username
        )
        self.wait.until(EC.presence_of_element_located((By.ID, "edit-pass"))).send_keys(
            self.password
        )
        self.wait.until(EC.presence_of_element_located((By.ID, "edit-submit"))).click()
        print("login")

    def navigate_to_demand_summary_page(self):
        """
        Navigates to the demand summary page by interacting with the menu elements.

        Depending on the environment (development or production), the method selects the appropriate
        menu elements to navigate to the demand summary page.
        """
        logging.info("Navigating to the demand summary page.")

        if config.DEBUG:
            menu_element = config.MENU_ELEMENT_DEV
            demand_element = config.DEMAND_ELEMENT_DEV
        else:
            menu_element = config.MENU_ELEMENT_PROD
            demand_element = config.DEMAND_ELEMENT_PROD

        logging.debug(
            "check_page_navigation elemtents with menu_element: %s, demand_element: %s",
            menu_element,
            demand_element,
        )

        parent_menu = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, menu_element))
        )
        actions = ActionChains(self.driver)
        actions.move_to_element(parent_menu).perform()

        demand_summary = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, demand_element))
        )
        demand_summary.click()
        print("Navigating")

    def navigate_each_customer_demand(self):
        """
        Handle radio button interactions on the webpage for faster processing.
        """
        for product in self.product_type:
            # CLICK WHICH PRODUCT : COMETS OR MAXCIM
            self.product = product
            radio_button = self.wait.until(
                EC.presence_of_element_located((By.ID, self.product_type[product]))
            )
            radio_button.click()

            table = self.driver.find_element(By.ID, "demandsumarydata")

            # Locate the tbody within the table
            tbody = table.find_element(By.TAG_NAME, "tbody")

            # ~ CHECK IF SET TO DEBUG. OTHERWISE GET ALL DEMANDS ITEMS
            if config.FOR_DEMO:
                # base_part_numbers_sample:dict = config.SAMPLE_BASE_PART_NUM

                rows = tbody.find_elements(By.TAG_NAME, "tr")
                row_texts = []

                # Extract all row texts first to minimize WebDriver calls
                for row in rows:
                    try:
                        row_texts.append(
                            row.find_element(By.CSS_SELECTOR, "td.nav a").text
                        )
                    except Exception as error:
                        print(f"Error processing row: {error}")

                # Filter rows using list comprehension
                selected_rows = [
                    row
                    for row, text in zip(rows, row_texts)
                    if any(part_num in text for part_num in config.SAMPLE_BASE_PART_NUM)
                ]
                rows = selected_rows
            else:
                rows = tbody.find_elements(By.TAG_NAME, "tr")

            # ~ PROCESS(ALLOCATE) EACH DEMAND ITEM(ROW).
            len_rows = len(rows)  # ~ ACTUAL NUMBER OF DEMANDS
            idx = 0
            list_partial_tp = (
                []
            )  # ~ RECORD PREVIOUSLY SEEN DEMAND ITEM THAT HAS PARTIAL REEL

            while len_rows > idx:
                try:
                    # ~ RELOCATE AGAIN EACH DEMAND ITEM. IT PREVENTS SELENIUM QUITING IF THERE IS ACCIDENTAL WEBPAGE RELOADING

                    table_d = self.driver.find_element(By.ID, "demandsumarydata")

                    # Locate the tbody within the table
                    tbody = table_d.find_element(By.TAG_NAME, "tbody")

                    if config.FOR_DEMO:
                        rows = tbody.find_elements(By.TAG_NAME, "tr")
                        row_texts = []

                        # Extract all row texts first to minimize WebDriver calls
                        for row in rows:
                            try:
                                row_texts.append(
                                    row.find_element(By.CSS_SELECTOR, "td.nav a").text
                                )
                            except Exception as error:
                                print(f"Error processing row: {error}")

                        # Filter rows using list comprehension
                        selected_rows = [
                            row
                            for row, text in zip(rows, row_texts)
                            if any(
                                part_num in text
                                for part_num in config.SAMPLE_BASE_PART_NUM
                            )
                        ]
                        rows = selected_rows
                    else:
                        rows = tbody.find_elements(By.TAG_NAME, "tr")

                    # ~ FOR THAT ROW(idx), CHECKS BASEPART NUMBER, IT THE DEMAND HAS PARTIAL REEL, AND ITS LINK.

                    # Locate the anchor tag within the row
                    anchor = rows[idx].find_element(By.CSS_SELECTOR, "td.nav a")

                    # Extract the href attribute to get the link
                    link = anchor.get_attribute("href")

                    base_part_num = anchor.text

                    # Locate the cell with the specific class
                    partial_reel = rows[idx].find_element(
                        By.CSS_SELECTOR,
                        "td.labelnum.partreelcnt, td.labelnum.partreelcnt.ispartreel",
                    )

                    # Extract the text from the cell
                    response = partial_reel.text

                    # ~ CHECK IF THAT BASE PART NUMBER DONT HAVE PARTIAL REEL, OTHERWISE IT WILL PROCEED TO NEXT BASEPART NUMBER.
                    if base_part_num in list_partial_tp:
                        idx += 1
                        continue  # Wont execute below self.faster_process_links
                    if response != "":
                        list_partial_tp.append(base_part_num)
                        idx += 1
                        continue

                    # ~ THIS EXECUTES ALLOCATION OF BASE PART NUMBER DEDICATED LINK
                    self.perform_allocation(link, base_part_num, product)

                    idx += 1
                except Exception as error:
                    return_button = self.driver.find_element(By.ID, "btn_return")
                    return_button.click()
                    time.sleep(1)
                    idx += 1
                    continue

    def check_and_return(self, elements):
        # Define the specific elements to check
        specific_elements = ["BDPACK-TR", "PACKLABEL", "TAPEREEL"]

        # Check if there's an element that is not in specific_elements
        for element in elements:
            if element not in specific_elements:
                return element

        # If no such element, check if "PACKLABEL" exists
        if "PACKLABEL" in elements:
            return "PACKLABEL"

        # If "PACKLABEL" also doesn't exist, return the remaining element
        # Assuming there's only one remaining element
        for element in elements:
            if element in specific_elements:
                return element

        # In case no elements match (should not happen as per the problem statement)
        return None
    # Function to sort the keys based on work week and year
    def sort_week_keys(self, week_keys):
        # Convert the keys to a sortable form (e.g., 'W49'23' becomes (23, 49))
        sortable_weeks = [
            (int(wk.split("'")[1]), int(wk[1:].split("'")[0])) for wk in week_keys
        ]
        # Sort by year first, then by week number
        sorted_weeks = sorted(sortable_weeks)
        # Convert back to the original format
        sorted_week_keys = [f"W{wk[1]:02}'{wk[0]:02}" for wk in sorted_weeks]
        # sorted_week_keys = []
        # for wk in sorted_weeks:
        #     if len(wk[1]) == 1:
        #         sorted_week_keys.append()
        return sorted_week_keys

    def sort_demands(self, demands):
        # Convert BSD to a sortable format assuming the format 'W##\'YY'
        for demand in demands:
            week, year = demand["BSD"].split("'")
            demand["Sort Key"] = int(year) * 52 + int(
                week[1:]
            )  # Calculate a sortable key
        # Sort demands based on the Sort Key, Finish Process, and Finish Type
        sorted_demands = sorted(
            demands,
            key=lambda x: (x["Sort Key"], x["Finish Process"], x["Finish Type"]),
        )
        return sorted_demands

    def allocate_supply(self, lot_qty, sorted_demands, product_type):
        allocations = []
        tape_reel_total = 0

        # Group demands by BSD
        demands_by_bsd = {}
        for demand in sorted_demands:
            bsd_key = demand["BSD"]
            if bsd_key not in demands_by_bsd:
                demands_by_bsd[bsd_key] = []
            demands_by_bsd[bsd_key].append(demand)

        # Sort demands within each BSD by the remaining balance in descending order
        for bsd_key in demands_by_bsd:
            demands_by_bsd[bsd_key].sort(
                key=lambda x: x["Remaining Balance"], reverse=True
            )

        # Allocate for each BSD
        allocated_part_num_tracker = []
        std_qty_tracker = []
        for bsd_key in self.sort_week_keys(demands_by_bsd.keys()):
            for demand in demands_by_bsd[bsd_key]:
                allocated_part_num_tracker.append(demand["Finish Part #"])#tracker
                if demand["Finish Process"] in ["BDPACK-TR", "PACKLABEL", "TAPEREEL"]:
                    if product_type == "MAXCIM":
                        demand["STD_QTY"] = demand["STD_QTY"] * (1.002)
                        min_allocated_qty = ceil((
                            min(lot_qty, demand["Remaining Balance"] * (1.002))
                            // demand["STD_QTY"]
                        ) * demand["STD_QTY"])
                        if demand["Remaining Balance"] >= min_allocated_qty:
                            allocated_qty = min(lot_qty, demand["Remaining Balance"])
                        else:
                            allocated_qty = min(lot_qty, min_allocated_qty)
                    else:
                        min_allocated_qty = ceil((
                            min(lot_qty, demand["Remaining Balance"])
                            // demand["STD_QTY"]
                        ) * demand["STD_QTY"])
                        if demand["Remaining Balance"] >= min_allocated_qty:
                            allocated_qty = min(lot_qty, demand["Remaining Balance"])
                        else:
                            allocated_qty = min(lot_qty, min_allocated_qty)
                    # current_std_qty = demand["STD_QTY"]
                    std_qty_tracker.append(demand["STD_QTY"])
                    tape_reel_total += allocated_qty
                else:
                    allocated_qty = min(lot_qty, demand["Remaining Balance"])

                lot_qty -= allocated_qty

                allocations.append(
                    {
                        "BSD": demand["BSD"],
                        "Finish Part #": demand["Finish Part #"],
                        "Finish Process": demand["Finish Process"],
                        "Allocated Qty": allocated_qty,
                        "STD_QTY": demand["STD_QTY"],
                        "Finish Type": demand["Finish Type"],
                    }
                )

                if lot_qty <= 0:
                    break
            if lot_qty <= 0:
                break

        print(allocations)
        num_remain_allocation = 0
        for allocation in allocations:
            if allocation["Allocated Qty"] != 0:
                num_remain_allocation += 1

        if num_remain_allocation != 1: #FULL or SPLIT
            # # Adjust TAPE REEL allocations if necessary
            # if tape_reel_total % tapereel_std_qty != 0:
            sums_by_part = {}
            for allocation in allocations:
                part = allocation["Finish Part #"]
                qty = allocation["Allocated Qty"]
                finish_proc = allocation["Finish Process"]
                finish_type = allocation["Finish Type"]
                if qty > 0:
                    if part in sums_by_part:
                        sums_by_part[part][0] += qty
                    else:
                        sums_by_part[part] = [qty, finish_proc, finish_type]

            surplus_units = 0
            for record in sums_by_part:
                if sums_by_part[record][1] in ["BDPACK-TR", "PACKLABEL", "TAPEREEL"]:
                    
                    
                    for allocation in allocations:
                        if record == allocation["Finish Part #"]:
                            if sums_by_part[record][0]%allocation["STD_QTY"] != 0:
                                difference = sums_by_part[record][0]%allocation["STD_QTY"]
                                sums_by_part[record][0] -= difference
                                surplus_units += difference
                                break
            alloc_fp_tuple = tuple(sums_by_part[key][1] for key in sums_by_part)

            not_std_elem = self.check_and_return(alloc_fp_tuple)

            for record in sums_by_part:
                if sums_by_part[record][1] == not_std_elem:
                    sums_by_part[record][0] += surplus_units
                    break
            


            # #{'MAX17613AATP+': [1634, 'LEADSCAN', 'STD'], 'MAX17613AATP+T': [56740, 'TAPEREEL', 'STD']}      
            # for allocation in allocations:
            #     if allocation["Finish Process"] in [
            #         "BDPACK-TR",
            #         "PACKLABEL",
            #         "TAPEREEL",
            #     ]:
            #         if allocation["Allocated Qty"] > allocation["STD_QTY"]:
            #             difference = tape_reel_total % tapereel_std_qty
            #             allocation["Allocated Qty"] -= difference
            #             tape_reel_total -= difference
            #             for allocation in reversed(allocations):
            #                 if allocation["Finish Process"] not in [
            #                     "BDPACK-TR",
            #                     "PACKLABEL",
            #                     "TAPEREEL",
            #                 ]:
            #                     allocation["Allocated Qty"] += difference
            #                     break
            #             if tape_reel_total % tapereel_std_qty == 0:
        
        
          #                 break
        else:
            sums_by_part = {}
            for allocation in allocations:
                part = allocation["Finish Part #"]
                qty = allocation["Allocated Qty"]
                finish_proc = allocation["Finish Process"]
                finish_type = allocation["Finish Type"]
                if qty > 0:
                    if part in sums_by_part:
                        sums_by_part[part][0] += qty
                    else:
                        sums_by_part[part] = [qty, finish_proc, finish_type]

        # allocations = adjust_tape_reel_allocations(allocations, std_qty)
        return sums_by_part

    def parse_demand_data_new(self, lst: list):
        # Initialize variables to store the indices

        dash_indices = []
        space_indices = []

        # Iterate over the list to find indices of '-' and ' '
        for i, item in enumerate(lst):
            if item == "-":
                dash_indices.append(i)
            elif item == " ":
                space_indices.append(i)

        # Pair the indices
        index_pairs = list(zip(dash_indices, space_indices))

        between_pairs = []

        # Iterate through the index pairs
        for i in range(len(index_pairs) - 1):
            # Start of the next range is one more than the end of the current range
            start = index_pairs[i][1] + 1
            # End of the next range is one less than the start of the following range
            end = index_pairs[i + 1][0] - 1
            between_pairs.append((start, end))

        # Add the last range, which goes from the end of the last pair to the end of the list
        if index_pairs:
            last_end = index_pairs[-1][1]
            if last_end < len(lst) - 1:
                between_pairs.append((last_end + 1, len(lst) - 1))

        # Iterate over header demand rows
        header_indexes = 0
        sub_rows_indexes = 1

        index_pairs = (index_pairs, between_pairs)
        # index_pairs = ([(0, 11), (22, 33)], [(12, 21), (34, 48)])
        # header_indexes = [(0, 11), (22, 33)]
        # sub_rows_indexes = [(12, 21), (34, 48)]
        data = []
        # std_qty_list = []
        for idx, (f_idx, l_idx) in enumerate(index_pairs[header_indexes]):
            # check packaging type
            # print(lst[f_idx:l_idx])
            FINISH_PROCESS = lst[f_idx + 4]
            fsub_idx, lsub_idx = index_pairs[sub_rows_indexes][idx]
            # STD_QTY = int(lst[f_idx + 5].replace(",", ""))
            # std_qty_list.append(STD_QTY)
            # print(fsub_idx, lsub_idx)
            for index, elem in enumerate(lst[fsub_idx:lsub_idx]):
                if "W" in elem:
                    # print(index)
                    # print(int(data[index+lsub_idx+3].replace(",","")))
                    FINISH_PART_NUM = lst[f_idx + 2]
                    FINISH_TYPE = lst[f_idx + 10]
                    BSD = lst[index + fsub_idx]
                    REMAINING_BALANCE = lst[index + fsub_idx + 3].replace(",", "")
                    try:
                        STD_QTY = int(lst[f_idx + 5].replace(",", ""))
                    except:
                        STD_QTY = 0
                    # raw_Ti_LS.append(lst[index + fsub_idx].replace("W", ""))
                    # D_LS.append(int(lst[index + fsub_idx + 3].replace(",", "")))
                    data.append(
                        {
                            "BSD": BSD,
                            "Finish Process": FINISH_PROCESS,
                            "Finish Type": FINISH_TYPE,
                            "Remaining Balance": int(REMAINING_BALANCE),
                            "Finish Part #": FINISH_PART_NUM,
                            "STD_QTY": STD_QTY,
                            # "Finish Type":
                        }
                    )

        return data

    def evaluate_allocation(self, input_dict):
        # Check if any of the values contain "CUST" as the last element
        contains_cust = any(value[-1] == "CUST" for value in input_dict.values())

        # Check the count of non-zero values
        non_zero_count = sum(1 for value in input_dict.values() if value[0] != 0)

        # If "CUST" is found or there's more than one non-zero value, return "SPLIT"
        if contains_cust or non_zero_count > 1:
            return "SPLIT"
        else:
            return "FULL"

    def evaluate_demands(self, input_list):
        # Flags and counters for conditions
        tapereel_std_count = 0
        leadscan_std_count = 0
        has_cust = False
        non_standard = False

        # Iterate through each dictionary in the list
        for item in input_list:
            finish_process = item["Finish Process"]
            finish_type = item["Finish Type"]

            # Count TAPEREEL and LEADSCAN with STD
            if finish_process == "TAPEREEL" and finish_type == "STD":
                tapereel_std_count += 1
            elif finish_process == "LEADSCAN" and finish_type == "STD":
                leadscan_std_count += 1

            # Check for CUST
            if finish_type == "CUST":
                has_cust = True

            # Check for non-standard types
            if finish_process not in ["TAPEREEL", "LEADSCAN"]:
                non_standard = True

        # Determine the categories
        categories = set()
        if has_cust:
            categories.add("Split CUST Special")
        if non_standard:
            categories.add("Maxcim")
        if tapereel_std_count > 0:
            categories.add("Full TR")
        if leadscan_std_count > 0:
            categories.add("Full LS")
        if tapereel_std_count > 0 and leadscan_std_count > 0:
            categories.add("Split TR")

        # Add "Split STD" if there are multiple occurrences or mixed types with STD
        if (
            tapereel_std_count > 1
            or leadscan_std_count > 1
            or (
                tapereel_std_count > 0
                and leadscan_std_count > 0
                and (tapereel_std_count + leadscan_std_count > 2)
            )
        ):
            categories.add("Split STD")

        return categories

    def perform_allocation(self, link, base_part_num, product):
        logging.info(f"Processing links with product type: {self.product}")

        # ~ CAREFULLY GO TO THE LINK. SCAN BASEPART# DEMANDS TABLE
        try:
            # click the link
            self.driver.get(link)

            # ~ SCAN BASEPART# DEMANDS TABLE
            demanditem_rows = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr.demanditem"))
            )

            demand_table = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "table.demanddata")
                )
            )

            to_save = False

            # print(
            #     f"Product Type: {self.product} Base Part Number: {base_part_num}",
            #     end=" ",
            # )
        except Exception:
            print("Problem on clicking demand item link on demand summary!")

        if len(demanditem_rows) == 1:  # 1 way demand
            # for i, row in enumerate(demanditem_rows):
            row, *_ = demanditem_rows
            try:
                # parsing demand table
                td_elements = WebDriverWait(row, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "td"))
                )

                row_data = [cell.text for cell in td_elements]

                _, _, _, _, finish_process, *_, finish_type = row_data

                if finish_process not in [
                    "TAPEREEL",
                    "LEADSCAN",
                    "PACKLABEL",
                    "BDPACK-TR",
                ]:
                    return

                # New block to extract data from the specific table
                try:
                    # Get items from wip table
                    item_rows = self.wait.until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, "tr.wiplotitem")
                        )
                    )

                    # Initialize a list to hold the data
                    # item_table_data = []
                    empty = ""
                    # iterate lot items
                    for row in item_rows:
                        # Locate the td elements within this row
                        td_elements = row.find_elements(By.TAG_NAME, "td")
                        # Extract text from each td element
                        # row_data = [td.text for td in td_elements]
                        action, lot_number, operation, *_, status, _ = [
                            td.text for td in td_elements
                        ]
                        print(
                            f"Product-Type: {self.product} Base-Part-Number: {base_part_num} Lot-Number: {lot_number}",
                            end=" ",
                        )
                        if (
                            action is empty
                            and status is empty
                            and int(operation) != 9790
                        ):
                            if any(
                                keyword in row_data[1]
                                for keyword in ["ENG", "NPI", "QUAL", "QUA"]
                            ) or lot_number.lower().startswith("z"):
                                continue  # Skip this tuple
                            to_save = True

                            try:
                                # Locate the dropdown within this row
                                dropdown = row.find_element(
                                    By.CSS_SELECTOR, "select.fintype"
                                )
                                # Create a Select object
                                select_dropdown = Select(dropdown)
                                # time.sleep(1)
                                logging.info(f"Base Part #: {base_part_num}")
                                if (
                                    finish_process == "TAPEREEL"
                                    and finish_type == "STD"
                                ):
                                    select_dropdown.select_by_visible_text("Full TR")
                                    select_value = "Full TR"
                                elif (
                                    finish_process == "LEADSCAN"
                                    and finish_type == "STD"
                                ):
                                    select_dropdown.select_by_visible_text("Full LS")
                                    select_value = "Full LS"
                                elif (
                                    finish_process == "PACKLABEL"
                                    and finish_type == "STD"
                                ):
                                    select_dropdown.select_by_visible_text("MaxCIM")
                                    select_value = "MaxCIM"
                                elif (
                                    finish_process == "BDPACK-TR"
                                    and finish_type == "STD"
                                ):
                                    select_dropdown.select_by_visible_text("Full TR")
                                    select_value = "Full TR"

                                elif finish_type == "CUST":
                                    select_dropdown.select_by_visible_text(
                                        "Split Cust Special"
                                    )
                                    select_value = "Split Cust Special"
                                logging.info(f"Selected dropdown value: {select_value}")
                                self.allocation_counter += 1
                            except Exception as e_dropdown:
                                print(
                                    f"An error occurred while interacting with the dropdown: {str(e_dropdown)}"
                                )

                    if to_save:
                        # Locate the "Save" button and click it
                        save_button = self.driver.find_element(By.ID, "btn_save")
                        save_button.click()
                        print("(Allocated Successfull)")
                    else:
                        print("")

                    # time.sleep(1)
                except Exception as e:
                    print("Problem on one-way demand allocation!")
                    print(
                        f"An error occurred while extracting item table data: {str(e)}"
                    )

            except Exception as e_inner:
                print(f"Problem on one way demand: {type(e_inner)}")

            return_button = self.driver.find_element(By.ID, "btn_return")
            return_button.click()
            time.sleep(1)

        
        else: #demanditem_Rows > 1
            for i, row in enumerate(demand_table):
                try:
                    # parsing demand table
                    td_elements = WebDriverWait(row, 10).until(
                        EC.presence_of_all_elements_located((By.TAG_NAME, "td"))
                    )
                    # extract demand data

                    all_data = [cell.text for cell in td_elements]
                    # print(all_data)

                    demands = self.parse_demand_data_new(all_data)

                except:
                    print(" Problem on parsing demand table")
                    continue

            # if std_proceed_allocation:
            try:
                # ~ CHECK AND PARSE WIP TABLE
                item_rows = self.wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "tr.wiplotitem")
                    )
                )

                num_rows = len(item_rows)  # ACTUAL NUMBER OF ROWS
                idx = 0
                empty = ""
                while num_rows > 0:
                    # ~ RUN THROUGH EACH WIP ITEM
                    demand_table = self.wait.until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, "table.demanddata")
                        )
                    )

                    # ~ PARSE DEMAND TABLE, IT HAS ONLY 1 VALUE.
                    for i, row in enumerate(demand_table):
                        try:
                            # parsing demand table
                            td_elements = WebDriverWait(row, 10).until(
                                EC.presence_of_all_elements_located((By.TAG_NAME, "td"))
                            )
                            # extract demand data

                            all_data = [cell.text for cell in td_elements]
                            parsed_data = self.parse_demand_data_new(all_data)

                        except:
                            print(" Problem on parsing demand table")
                            continue

                    # Get items from wip table
                    item_rows = self.wait.until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, "tr.wiplotitem")
                        )
                    )

                    td_elements = item_rows[idx].find_elements(By.TAG_NAME, "td")
                    row_data = [td.text for td in td_elements]
                    action, lot_number, operation, *_, status, _ = [
                        td.text for td in td_elements
                    ]
                    # print(
                    #     f"Product Type: {self.product_type} Base Part Number: {base_part_num}"
                    # )
                    # row 0 = action status  row 14 = allocation status row 2 = operation status
                    print(
                        f"Product-Type: {self.product} Base-Part-Number: {base_part_num} Lot-Number: {lot_number}",
                        end=" ",
                    )
                    if action is empty and status is empty and int(operation) != 9790:
                        # logging.info(
                        #     f"Current link: {link}, base_part_num: {base_part_num}"
                        # )
                        if any(
                            keyword in row_data[1]
                            for keyword in ["ENG", "NPI", "QUAL", "QUA"]
                        ) or lot_number.lower().startswith("z"):
                            num_rows -= 1
                            continue

                        to_save = True
                        # item_table_data.append(row_data[:4])

                        lot_qty = int(row_data[3].replace(",", ""))

                        sorted_demand_data = self.sort_demands(parsed_data)
                        print(sorted_demand_data)
                        # possible_allocation = self.evaluate_demands(sorted_demand_data)
                        # print(possible_allocation)
                        sums_by_part = self.allocate_supply(
                            lot_qty, sorted_demand_data, product
                        )

                        # sums_by_part = {}
                        # for allocation in allocations:
                        #     part = allocation["Finish Part #"]
                        #     qty = allocation["Allocated Qty"]
                        #     finish_proc = allocation["Finish Process"]
                        #     finish_type = allocation["Finish Type"]
                        #     if qty > 0:
                        #         if part in sums_by_part:
                        #             sums_by_part[part][0] += qty
                        #         else:
                        #             sums_by_part[part] = [qty, finish_proc, finish_type]

                        print(sums_by_part)

                        alloc_category = self.evaluate_allocation(
                            sums_by_part
                        )  # FUll or SPLIT

                        # allocation_finish_process = {}
                        # for allocation in allocations:
                        #     allocation_finish_process[
                        #         allocation["Finish Part #"]
                        #     ] = allocation["Finish Process"]
                        # Code to interact with the dropdown and select 'FULL_TR'

                        try:
                            # Locate the dropdown within this row
                            # Get items from wip table

                            dropdown = item_rows[idx].find_element(
                                By.CSS_SELECTOR, "select.fintype"
                            )
                            # Create a Select object
                            select_dropdown = Select(dropdown)

                            # List to hold the text of visible options
                            visible_options_text = []

                            # Iterate over all options in the dropdown
                            for option in select_dropdown.options:
                                # Check if the option is visible (i.e., not having 'display: none')
                                if option.get_attribute("style") != "display: none;":
                                    # Add the text of the option to the list
                                    visible_options_text.append(option.text)
                            # time.sleep(1)

                            allocation_record_matrix = {
                                "FULL": {
                                    "TAPEREEL": "Full TR",
                                    "LEADSCAN": "Full LS",
                                    "BDPACK-TR": "Full TR",
                                    "BDPACK-LS": "Full LS",
                                    "PACKLABEL": "MaxCIM",
                                },
                                "SPLIT": [
                                    "Split TR",
                                    "Split Cust Special",
                                    "MaxCIM",
                                    "Split Standard",
                                ],
                            }
                            # common_option = list(
                            #     set(visible_options_text).intersection(
                            #         set(allocation_record_matrix[alloc_category])
                            #     )
                            # )
                            logging.info(f"Base Part #: {base_part_num}")

                            # Using if/else for decision making
                            if alloc_category == "FULL":
                                if self.product == "MAXCIM":
                                    common_option = list(
                                        set(visible_options_text).intersection(
                                            set(["Full TR", "Full LS"])
                                        )
                                    )
                                    print(common_option)

                                # Process the input to create the desired output, excluding records with zero values
                                # {"TAPEREEL":1213123}
                                output_data = {
                                    details[1]: details[0]
                                    for details in sums_by_part.values()
                                    if details[0] != 0
                                }
                                fp = list(output_data.keys())[0]  # TAPEREEL
                                common_option1 = allocation_record_matrix[
                                    alloc_category
                                ][fp]

                                if self.product == "COMETS":
                                    select_dropdown.select_by_visible_text(
                                        common_option1
                                    )
                                    select_value = "Full"
                                
                                else:
                                    if common_option[0] == common_option1:
                                        select_dropdown.select_by_visible_text(
                                            common_option1
                                        )
                                        select_value = "Full"
                                    elif (
                                        common_option[0] != common_option1
                                        or common_option1 == "MaxCIM"
                                    ):
                                        select_dropdown.select_by_visible_text("MaxCIM")
                                        select_value = "MaxCIM"
                                        allocation_dropdown = {
                                            details[1]: details[0]
                                            for details in sums_by_part.values()
                                        }

                                        # TR_allocation = int(allocation_dropdown["TAPEREEL"])
                                        # LS_allocation = int(allocation_dropdown["LEADSCAN"])

                                        num_allocation = len(sums_by_part.keys())
                                        for i in range(num_allocation - 1):
                                            row_span_newitem = item_rows[idx].find_element(
                                                By.CSS_SELECTOR, "span.act_newitem"
                                            )
                                            row_span_newitem.click()
                                        for alloc_idx, FINISH_PART_NUM in enumerate(
                                            sums_by_part
                                        ):
                                            if alloc_idx == 0:
                                                finish_partnum_dropdown = item_rows[
                                                    idx
                                                ].find_element(
                                                    By.CSS_SELECTOR, "select.finpartnum"
                                                )
                                                dropdown_part_num = FINISH_PART_NUM
                                                select_dropdown = Select(
                                                    finish_partnum_dropdown
                                                )
                                                select_dropdown.select_by_visible_text(
                                                    dropdown_part_num
                                                )

                                                allocation_cell1 = item_rows[
                                                    idx
                                                ].find_element(
                                                    By.CSS_SELECTOR, "input.allocqty"
                                                )
                                                allocation_cell1.send_keys(
                                                    int(sums_by_part[FINISH_PART_NUM][0])
                                                )
                                            else:
                                                new_row_xpath = f"//tr[contains(@id, 'rowtmp__{alloc_idx}')]"
                                                self.wait.until(
                                                    EC.presence_of_element_located(
                                                        (By.XPATH, new_row_xpath)
                                                    )
                                                )
                                                new_row = self.driver.find_element(
                                                    By.XPATH, new_row_xpath
                                                )

                                                new_finish_type_dropdown = (
                                                    new_row.find_element(
                                                        By.CSS_SELECTOR, "select.fintype"
                                                    )
                                                )

                                                select_dropdown = Select(
                                                    new_finish_type_dropdown
                                                )
                                                select_dropdown.select_by_visible_text(
                                                    "MaxCIM"
                                                )
                                                select_value = "MaxCIM"

                                                new_finish_partnum_dropdown = (
                                                    new_row.find_element(
                                                        By.CSS_SELECTOR, "select.finpartnum"
                                                    )
                                                )
                                                dropdown_part_num = FINISH_PART_NUM
                                                select_dropdown = Select(
                                                    new_finish_partnum_dropdown
                                                )
                                                select_dropdown.select_by_visible_text(
                                                    dropdown_part_num
                                                )

                                                allocation_cell2 = new_row.find_element(
                                                    By.CSS_SELECTOR, "input.allocqty"
                                                )
                                                allocation_cell2.send_keys(
                                                    int(sums_by_part[FINISH_PART_NUM][0])
                                                )

                            elif alloc_category == "SPLIT":
                                common_option = list(
                                    set(visible_options_text).intersection(
                                        set(allocation_record_matrix[alloc_category])
                                    )
                                )
                                if common_option[0] == "Split TR":
                                    select_dropdown.select_by_visible_text("Split TR")
                                    select_value = "SPLIT_TR"
                                    allocation_dropdown = {
                                        details[1]: details[0]
                                        for details in sums_by_part.values()
                                    }

                                    if "TAPEREEL" in allocation_dropdown:
                                        TR_allocation = int(
                                            allocation_dropdown["TAPEREEL"]
                                        )

                                    if "BDPACK-TR" in allocation_dropdown:
                                        TR_allocation = int(
                                            allocation_dropdown["BDPACK-TR"]
                                        )

                                    if "LEADSCAN" in allocation_dropdown:
                                        LS_allocation = int(
                                            allocation_dropdown["LEADSCAN"]
                                        )

                                    if "BDPACK-LS" in allocation_dropdown:
                                        LS_allocation = int(
                                            allocation_dropdown["BDPACK-LS"]
                                        )

                                    allocation_cell1 = item_rows[idx].find_element(
                                        By.CSS_SELECTOR, "input.allocqty"
                                    )
                                    allocation_cell1.send_keys(TR_allocation)

                                    new_row_xpath = "//tr[contains(@id, 'rowtmp__')]"
                                    self.wait.until(
                                        EC.presence_of_element_located(
                                            (By.XPATH, new_row_xpath)
                                        )
                                    )
                                    new_row = self.driver.find_element(
                                        By.XPATH, new_row_xpath
                                    )
                                    allocation_cell2 = new_row.find_element(
                                        By.CSS_SELECTOR, "input.allocqty"
                                    )
                                    allocation_cell2.send_keys(LS_allocation)

                                    print(f"Number of rows: {num_rows}")
                                    # num_rows += 1
                                    idx += 1
                                elif common_option[0] == "Split Cust Special":
                                    select_dropdown.select_by_visible_text(
                                        "Split Cust Special"
                                    )
                                    select_value = "Split Cust Special"
                                    allocation_dropdown = {
                                        details[1]: details[0]
                                        for details in sums_by_part.values()
                                    }

                                    # TR_allocation = int(allocation_dropdown["TAPEREEL"])
                                    # LS_allocation = int(allocation_dropdown["LEADSCAN"])

                                    num_allocation = len(sums_by_part.keys())
                                    for i in range(num_allocation - 1):
                                        row_span_newitem = item_rows[idx].find_element(
                                            By.CSS_SELECTOR, "span.act_newitem"
                                        )
                                        row_span_newitem.click()
                                    for alloc_idx, FINISH_PART_NUM in enumerate(
                                        sums_by_part
                                    ):
                                        if alloc_idx == 0:
                                            finish_partnum_dropdown = item_rows[
                                                idx
                                            ].find_element(
                                                By.CSS_SELECTOR, "select.finpartnum"
                                            )
                                            dropdown_part_num = FINISH_PART_NUM
                                            select_dropdown = Select(
                                                finish_partnum_dropdown
                                            )
                                            select_dropdown.select_by_visible_text(
                                                dropdown_part_num
                                            )

                                            allocation_cell1 = item_rows[
                                                idx
                                            ].find_element(
                                                By.CSS_SELECTOR, "input.allocqty"
                                            )
                                            allocation_cell1.send_keys(
                                                int(sums_by_part[FINISH_PART_NUM][0])
                                            )
                                        else:
                                            new_row_xpath = f"//tr[contains(@id, 'rowtmp__{alloc_idx}')]"
                                            self.wait.until(
                                                EC.presence_of_element_located(
                                                    (By.XPATH, new_row_xpath)
                                                )
                                            )
                                            new_row = self.driver.find_element(
                                                By.XPATH, new_row_xpath
                                            )

                                            new_finish_type_dropdown = (
                                                new_row.find_element(
                                                    By.CSS_SELECTOR, "select.fintype"
                                                )
                                            )

                                            select_dropdown = Select(
                                                new_finish_type_dropdown
                                            )
                                            select_dropdown.select_by_visible_text(
                                                "Split Cust Special"
                                            )
                                            select_value = "MaxCIM"

                                            new_finish_partnum_dropdown = (
                                                new_row.find_element(
                                                    By.CSS_SELECTOR, "select.finpartnum"
                                                )
                                            )
                                            dropdown_part_num = FINISH_PART_NUM
                                            select_dropdown = Select(
                                                new_finish_partnum_dropdown
                                            )
                                            select_dropdown.select_by_visible_text(
                                                dropdown_part_num
                                            )

                                            allocation_cell2 = new_row.find_element(
                                                By.CSS_SELECTOR, "input.allocqty"
                                            )
                                            allocation_cell2.send_keys(
                                                int(sums_by_part[FINISH_PART_NUM][0])
                                            )

                                elif common_option[0] == "MaxCIM":
                                    select_dropdown.select_by_visible_text("MaxCIM")
                                    select_value = "MaxCIM"
                                    allocation_dropdown = {
                                        details[1]: details[0]
                                        for details in sums_by_part.values()
                                    }

                                    # TR_allocation = int(allocation_dropdown["TAPEREEL"])
                                    # LS_allocation = int(allocation_dropdown["LEADSCAN"])

                                    num_allocation = len(sums_by_part.keys())
                                    for i in range(num_allocation - 1):
                                        row_span_newitem = item_rows[idx].find_element(
                                            By.CSS_SELECTOR, "span.act_newitem"
                                        )
                                        row_span_newitem.click()
                                    for alloc_idx, FINISH_PART_NUM in enumerate(
                                        sums_by_part
                                    ):
                                        if alloc_idx == 0:
                                            finish_partnum_dropdown = item_rows[
                                                idx
                                            ].find_element(
                                                By.CSS_SELECTOR, "select.finpartnum"
                                            )
                                            dropdown_part_num = FINISH_PART_NUM
                                            select_dropdown = Select(
                                                finish_partnum_dropdown
                                            )
                                            select_dropdown.select_by_visible_text(
                                                dropdown_part_num
                                            )

                                            allocation_cell1 = item_rows[
                                                idx
                                            ].find_element(
                                                By.CSS_SELECTOR, "input.allocqty"
                                            )
                                            allocation_cell1.send_keys(
                                                int(sums_by_part[FINISH_PART_NUM][0])
                                            )
                                        else:
                                            new_row_xpath = f"//tr[contains(@id, 'rowtmp__{alloc_idx}')]"
                                            self.wait.until(
                                                EC.presence_of_element_located(
                                                    (By.XPATH, new_row_xpath)
                                                )
                                            )
                                            new_row = self.driver.find_element(
                                                By.XPATH, new_row_xpath
                                            )

                                            new_finish_type_dropdown = (
                                                new_row.find_element(
                                                    By.CSS_SELECTOR, "select.fintype"
                                                )
                                            )

                                            select_dropdown = Select(
                                                new_finish_type_dropdown
                                            )
                                            select_dropdown.select_by_visible_text(
                                                "MaxCIM"
                                            )
                                            select_value = "MaxCIM"

                                            new_finish_partnum_dropdown = (
                                                new_row.find_element(
                                                    By.CSS_SELECTOR, "select.finpartnum"
                                                )
                                            )
                                            dropdown_part_num = FINISH_PART_NUM
                                            select_dropdown = Select(
                                                new_finish_partnum_dropdown
                                            )
                                            select_dropdown.select_by_visible_text(
                                                dropdown_part_num
                                            )

                                            allocation_cell2 = new_row.find_element(
                                                By.CSS_SELECTOR, "input.allocqty"
                                            )
                                            allocation_cell2.send_keys(
                                                int(sums_by_part[FINISH_PART_NUM][0])
                                            )
                                elif common_option[0] == "Split Standard":
                                    select_dropdown.select_by_visible_text("Split Standard")
                                    select_value = "Split Standard"
                                    allocation_dropdown = {
                                        details[1]: details[0]
                                        for details in sums_by_part.values()
                                    }

                                    # TR_allocation = int(allocation_dropdown["TAPEREEL"])
                                    # LS_allocation = int(allocation_dropdown["LEADSCAN"])

                                    num_allocation = len(sums_by_part.keys())
                                    for i in range(num_allocation - 1):
                                        row_span_newitem = item_rows[idx].find_element(
                                            By.CSS_SELECTOR, "span.act_newitem"
                                        )
                                        row_span_newitem.click()
                                    for alloc_idx, FINISH_PART_NUM in enumerate(
                                        sums_by_part
                                    ):
                                        if alloc_idx == 0:
                                            finish_partnum_dropdown = item_rows[
                                                idx
                                            ].find_element(
                                                By.CSS_SELECTOR, "select.finpartnum"
                                            )
                                            dropdown_part_num = FINISH_PART_NUM
                                            select_dropdown = Select(
                                                finish_partnum_dropdown
                                            )
                                            select_dropdown.select_by_visible_text(
                                                dropdown_part_num
                                            )

                                            allocation_cell1 = item_rows[idx].find_element(
                                                By.CSS_SELECTOR, "input.allocqty"
                                            )
                                            allocation_cell1.send_keys(
                                                int(sums_by_part[FINISH_PART_NUM][0])
                                            )
                                        else:
                                            new_row_xpath = f"//tr[contains(@id, 'rowtmp__{alloc_idx}')]"
                                            self.wait.until(
                                                EC.presence_of_element_located(
                                                    (By.XPATH, new_row_xpath)
                                                )
                                            )
                                            new_row = self.driver.find_element(
                                                By.XPATH, new_row_xpath
                                            )

                                            new_finish_type_dropdown = new_row.find_element(
                                                By.CSS_SELECTOR, "select.fintype"
                                            )

                                            select_dropdown = Select(
                                                new_finish_type_dropdown
                                            )
                                            select_dropdown.select_by_visible_text(
                                                "Split Standard"
                                            )
                                            select_value = "Split Standard"

                                            new_finish_partnum_dropdown = (
                                                new_row.find_element(
                                                    By.CSS_SELECTOR, "select.finpartnum"
                                                )
                                            )
                                            dropdown_part_num = FINISH_PART_NUM
                                            select_dropdown = Select(
                                                new_finish_partnum_dropdown
                                            )
                                            select_dropdown.select_by_visible_text(
                                                dropdown_part_num
                                            )

                                            allocation_cell2 = new_row.find_element(
                                                By.CSS_SELECTOR, "input.allocqty"
                                            )
                                            allocation_cell2.send_keys(
                                                int(sums_by_part[FINISH_PART_NUM][0])
                                            )

                            else:
                                print("Allocation is not working")

                            logging.info(f"Selected dropdown value: {select_value}")
                            self.allocation_counter += 1

                        except Exception as e_dropdown:
                            print(
                                f"An error occurred while interacting with the dropdown: {str(e_dropdown)}"
                            )
                    if to_save:
                        # Locate the "Save" button and click it
                        save_button = self.driver.find_element(By.ID, "btn_save")
                        save_button.click()
                        time.sleep(1)
                        print("(Allocated Successfull)")

                        # logging.info("Save successful.")
                    num_rows -= 1
                    idx += 1
                # time.sleep(1)
            except Exception as e:
                print("Problem on two-way allocation.")
                print(f"An error occurred while extracting item table data: {str(e)}")

            return_button = self.driver.find_element(By.ID, "btn_return")
            return_button.click()
            time.sleep(1)
        print("")

    def cleanup(self):
        """
        Closes the browser and properly ends the WebDriver session.

        This method waits for a brief period to ensure that all actions are complete
        before closing the browser. It then calls quit() on the WebDriver to properly
        terminate the session.

        Note:
            This method includes a fixed 1-second sleep to mitigate the risk of prematurely
            closing the browser before all actions are completed. Adjust this duration
            if necessary based on the specific requirements of the web interactions.
        """
        logging.info(f"{self.__class__.__name__}.cleanup method called")
        time.sleep(1)
        self.driver.quit()


def main():
    """
    Sequences of web actions to automate allocation.
    """
    web_actions = WebActions()
    try:
        web_actions.login()
        # Add more actions here
        web_actions.navigate_to_demand_summary_page()
        web_actions.navigate_each_customer_demand()
    except Exception as error:
        print(error)
    finally:
        web_actions.cleanup()


if __name__ == "__main__":
    main()
