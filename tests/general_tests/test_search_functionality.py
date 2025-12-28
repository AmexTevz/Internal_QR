import pytest
import pytest_check as check
import allure
from src.pages.store.menu_page import MenuPage
from src.data.endpoints.close_table import close_table
from datetime import datetime


TABLES = [3]


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.search
@pytest.mark.functional
@pytest.mark.all
@allure.feature("Menu")
@allure.story("Search")
@allure.title("Search for Menu Items by Name")
def test_search_functionality(browser_factory, endpoint_setup, table):
    timestamp = datetime.now().strftime("%B %d, %Y %H:%M")
    allure.dynamic.title(f"Search for Menu Items by Name - {timestamp}")
    [chrome] = browser_factory("chrome")
    menu_page = MenuPage(chrome)

    try:
        menu_page.navigate_to_main_menu()

        # ========================================
        # PART 1: Keyword Search Test
        # ========================================
        with allure.step("Test 1: Search by keywords"):
            keywords = ["juice", "salmon", "sandwich", "egg", "soup"]
            results = menu_page.search_multiple_keywords(keywords)

            # Summary for Allure
            summary = []

            for keyword, texts in results.items():
                with allure.step(f"Results for '{keyword}'"):
                    # Check 1: Results found
                    if len(texts) == 0:
                        check.fail(f"❌ '{keyword}' - No results found")
                        summary.append(f"❌ '{keyword}' - No results")
                        continue

                    # Check 2: Verify each result contains keyword
                    failed_results = []
                    passed_count = 0

                    for idx, text in enumerate(texts, start=1):
                        # Truncate long text for display
                        display_text = text[:50] + "..." if len(text) > 50 else text

                        if keyword.lower() in text.lower():
                            passed_count += 1
                        else:
                            failed_results.append(f"  Result {idx}: {display_text}")
                            check.fail(f"❌ '{keyword}' missing in result {idx}: {display_text}")

                    # Summary for this keyword
                    if failed_results:
                        summary.append(f"❌ '{keyword}' - {passed_count}/{len(texts)} passed")
                        allure.attach(
                            "\n".join(failed_results),
                            name=f"Failed Results for '{keyword}'",
                            attachment_type=allure.attachment_type.TEXT
                        )
                    else:
                        summary.append(f"✅ '{keyword}' - All {len(texts)} results passed")

            # Attach overall summary
            allure.attach(
                "\n".join(summary),
                name="Keyword Search Results Summary",
                attachment_type=allure.attachment_type.TEXT
            )

        # ========================================
        # PART 2: Random Item Exact Name Search Test
        # ========================================
        with allure.step("Test 2: Search by exact item names"):
            # Get 5 random menu items
            random_items = menu_page.get_random_menu_items_for_search(num_items=5)

            check.greater(
                len(random_items),
                0,
                "Failed to select any random items for search testing"
            )

            # Test each random item
            exact_search_summary = []

            for item in random_items:
                item_name = item['name']
                item_id = item['id']

                with allure.step(f"Search for exact name: '{item_name}'"):
                    search_result = menu_page.search_and_verify_first_result(item_name)

                    # Check 1: Search was performed
                    check.is_true(
                        search_result['searched'],
                        f"Failed to perform search for '{item_name}'"
                    )

                    # Check 2: Results were found
                    check.is_true(
                        search_result['results_found'],
                        f"No results found when searching for '{item_name}'"
                    )

                    # Check 3: Item is first in results (MAIN TEST)
                    if search_result['results_found']:
                        check.is_true(
                            search_result['is_first'],
                            f"❌ '{item_name}' is NOT first result. "
                            f"First result is '{search_result['first_result_name']}'"
                        )

                        if search_result['is_first']:
                            exact_search_summary.append(
                                f"✅ '{item_name}' - First in {search_result['total_results']} results"
                            )
                        else:
                            exact_search_summary.append(
                                f"❌ '{item_name}' - First result: '{search_result['first_result_name']}'"
                            )

            # Attach summary
            allure.attach(
                "\n".join(exact_search_summary),
                name="Exact Name Search Results Summary",
                attachment_type=allure.attachment_type.TEXT
            )

    except Exception as e:
        with allure.step("ERROR"):
            close_table()
            print(f"Error: {str(e)}")
            raise