from instagram_bot import create_driver, login, monitor_groups

def main():
    driver = create_driver()
    login(driver)
    while True:
        monitor_groups(driver)
        time.sleep(10)

if __name__ == "__main__":
    main()
