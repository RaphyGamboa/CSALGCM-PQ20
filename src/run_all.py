# run_all.py - run the full pipeline, every time.

import clean_data
import text_process
# import find_spelling_variants
# import write_csv

def main() -> None:
    print("== clean_data =="); clean_data.main()
    print("== text_process =="); text_process.main()
    # print("== find_variants =="); find_spelling_variants.main()
    # print("== write_csv =="); write_csv.main()
    print("done.")

if __name__ == "__main__":
    main()