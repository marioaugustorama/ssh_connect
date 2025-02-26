import curses

def test(stdscr):
    stdscr.clear()
    stdscr.addstr(5, 10, "Teste de curses funcionando!")
    stdscr.refresh()
    stdscr.getch()

curses.wrapper(test)

