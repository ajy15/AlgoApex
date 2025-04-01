import src.stockinfo.bot as bot
import src.account.info as info
import src.account.positions as positions
import src.order.order as order

def main():
    bot.getSPY()
    order.marketbuy('SPY', 1)
    positions.getall()
    info.print_info()

if __name__ == '__main__':
    main()