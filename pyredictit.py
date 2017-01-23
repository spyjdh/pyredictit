import datetime
import mechanicalsoup
import re

class Contract:
    def __init__(self, market, cid, name, type_, shares, avg_price, buy_offers, sell_offers, gain_loss, latest, buy, sell):
        self.timestamp = datetime.datetime.now()
        self.market = market
        self.cid = cid
        self.name = name
        self.type_ = type_
        self.number_of_shares = int(shares)
        self.avg_price = avg_price
        self.buy_offers = buy_offers
        self.sell_offers = sell_offers
        self.gain_loss = gain_loss
        if '(' in self.gain_loss:
            self.gain_loss = gain_loss.replace('(', '-').replace(')', '')
        self.latest = latest
        self.buy = buy
        self.sell = sell

    @property
    def shares(self):
        if self.number_of_shares == 1:
            return f"You have {self.number_of_shares} {self.type_} share."
        else:
            return f"You have {self.number_of_shares} {self.type_} shares."

    @property
    def average_price(self):
        return f"Your average purchase price of {self.type_} shares is {self.avg_price}"

    @property
    def gain_or_loss(self):
        if '+' in self.gain_loss:
            return f"Your shares have gained {self.gain_loss} in value."
        else:
            return f"Your shares have lost {self.gain_loss} in value."

    @property
    def sell_price(self):
        return f"{self.type_} shares are currently being bought for {self.sell}"

    @property
    def buy_price(self):
        return f"{self.type_} shares are currently being sold at {self.buy}"

    @property
    def estimate_sale_of_current_shares(self):
        try:
            if float(self.sell[:-1]) - float(self.avg_price[:-1]) > 0:
                return f"If you sold all of your shares now, you would earn ${str(float(float(self.sell[:-1]) - float(self.avg_price[:-1])) * self.number_of_shares * 0.01)}"
            else:
                return f"If you sold all of your shares now, you would lose ${str(float(float(self.sell[:-1]) - float(self.avg_price[:-1])) * self.number_of_shares * 0.01 + (float(self.number_of_shares) * float(self.average_price)))}"
        except ValueError:
            return "Contract has ended."

    @property
    def estimate_best_result(self):
        return f"If this contract resolves to {self.type_}, you would earn ${(1 - float(self.avg_price[:1])) * self.number_of_shares * 0.01 * -1}. Otherwise, you would lose ${float(self.avg_price[:1]) * self.number_of_shares * 0.01 * -1 - (float(self.number_of_shares) * float(self.avg_price[:-1])) * 0.01}}}"

    @property
    def implied_odds(self):
        return f"The implied odds of this contract resolving to {self.type_} are {self.buy.replace('¢', '%')}"

    def summary(self):
        print('----')
        print(self.timestamp)
        print(self.market)
        print(self.name)
        print(self.shares)
        print(self.gain_or_loss)
        print(self.average_price)
        print(self.buy_price)
        print(self.sell_price)
        print(self.estimate_sale_of_current_shares)
        print(self.implied_odds)
        print(self.estimate_best_result)
        print('-----')

    def update(self, api):
        my_shares = api.authed_session.get('https://www.predictit.org/Profile/GetSharesAjax')
        for market in my_shares.soup.find_all('table', class_='table table-striped table-center'):
            market_title = market.previous_element.previous_element.find('div', class_='outcome-title').find('a').get(
                'title')
            if market_title == self.market:
                market_data = [i.text.strip().replace(
                    "\n", "").replace("    ", "").replace('\r', '') for i in market.find_all('td')]
                market_data_lists = [market_data[x:x + 10] for x in range(0, len(market_data), 10)]
                cid = None
                for list in market_data_lists:
                    parsed_market_data = [market_title]
                    for string in list:
                        try:
                            cid = re.search(
                                pattern='#\w+\-(\d+)', string=string
                            ).group(1)
                            string = re.search(
                                pattern='(.*)\$\(.*\)\;', string=string
                            ).group(1)
                        except AttributeError:
                            pass
                        parsed_market_data.append(string)
                    parsed_market_data.insert(1, cid)
                    self.timestamp = datetime.datetime.now()
                    self.avg_price = parsed_market_data[5]
                    self.gain_loss = parsed_market_data[8]
                    self.latest = parsed_market_data[9]
                    self.buy = parsed_market_data[-2]
                    self.sell = parsed_market_data[-1]
                    break
            else:
                continue

    def buy_shares(self, api, number_of_shares, buy_price):
        if self.type_.lower() == 'no':
            type_, id_ = 'Short', '0'
        elif self.type_.lower() == 'yes':
            type_, id_ = 'Long', '1'
        load_side_page = api.browser.get(f'https://www.predictit.org/Trade/LoadBuy{type_}?contractId={self.cid}')
        token = load_side_page.soup.find('input', attrs={'name': '__RequestVerificationToken'}).get('value')
        r = api.browser.post('https://www.predictit.org/Trade/SubmitTrade',
                              {'__RequestVerificationToken': token,
                               'BuySellViewModel.ContractId': self.cid,
                               'BuySellViewModel.TradeType': id_,
                               'BuySellViewModel.Quantity': number_of_shares,
                               'BuySellViewModel.PricePerShare': f'{float(buy_price)}',
                               'X-Requested-With': 'XMLHttpRequest'})
        if str(r.status_code) == '200':
            print('Purchase successful!')

    def sell_shares(self, api, number_of_shares, sell_price):
        if self.type_.lower() == 'no':
            type_, id_ = 'Short', '0'
        elif self.type_.lower() == 'yes':
            type_, id_ = 'Long', '1'
        load_side_page = api.browser.get(f'https://www.predictit.org/Trade/LoadSell{type_}?contractId={self.cid}')
        token = load_side_page.soup.find('input', attrs={'name': '__RequestVerificationToken'}).get('value')
        r = api.browser.post('https://www.predictit.org/Trade/SubmitTrade',
                              {'__RequestVerificationToken': token,
                               'BuySellViewModel.ContractId': self.cid,
                               'BuySellViewModel.TradeType': id_,
                               'BuySellViewModel.Quantity': number_of_shares,
                               'BuySellViewModel.PricePerShare': f'{float(sell_price)}',
                               'X-Requested-With': 'XMLHttpRequest'})
        if str(r.status_code) == '200':
            print('Sale successful!')


    def __str__(self):
        return f"{self.market}, {self.name}, {self.type_}, {self.shares}, {self.average_price}, {self.buy_offers},{self.sell_offers}, {self.gain_loss}, {self.latest}, {self.buy}, {self.sell}"


class pyredictit:
    def __init__(self):
        self.my_contracts = None
        self.gain_loss = None
        self.browser = mechanicalsoup.Browser()
        self.authed_session = self.create_authed_session

    def current_gain_loss(self):
        my_shares_page = self.browser.get('https://www.predictit.org/Profile/MyShares')
        self.gain_loss = my_shares_page.soup.find("span", class_='SPShares').text
        print(self.gain_loss)


    def create_authed_session(self, username, password):
        login_page = self.browser.get('https://www.predictit.org/')
        login_form = login_page.soup.find('form', id='loginForm')
        login_form.select('#Email')[0]['value'] = username
        login_form.select('#Password')[0]['value'] = password
        logged_in_session = self.browser.submit(login_form, login_page.url)
        return self.browser

    def get_my_contracts(self):
        self.my_contracts = []
        my_shares = self.authed_session.get('https://www.predictit.org/Profile/GetSharesAjax')
        for market in my_shares.soup.find_all('table', class_='table table-striped table-center'):
            market_title = market.previous_element.previous_element.find('div', class_='outcome-title').find('a').get(
                'title')
            market_data = [i.text.strip().replace(
                "\n", "").replace("    ", "").replace('\r', '') for i in market.find_all('td')]
            market_data_lists = [market_data[x:x + 10] for x in range(0, len(market_data), 10)]
            cid = None
            for list in market_data_lists:
                parsed_market_data = [market_title]
                for string in list:
                    try:
                        cid = re.search(
                            pattern='#\w+\-(\d+)', string=string
                        ).group(1)
                        string = re.search(
                            pattern='(.*)\$\(.*\)\;', string=string
                        ).group(1)
                    except AttributeError:
                        pass
                    parsed_market_data.append(string)
                parsed_market_data.insert(1, cid)
                contract = Contract(*parsed_market_data)
                self.my_contracts.append(contract)

    def list_my_contracts(self):
        for contract in self.my_contracts:
            print('------')
            print(contract.timestamp)
            print(contract.market)
            print(contract.name)
            print(contract.shares)
            print(contract.gain_or_loss)
            print(contract.average_price)
            print(contract.buy_price)
            print(contract.sell_price)
            print(contract.estimate_sale_of_current_shares)
            print(contract.implied_odds)
            print(contract.estimate_best_result)
            print('------')

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

if __name__ == '__main__':
    predict_it_api = pyredictit()
    predict_it_api.create_authed_session()
    predict_it_api.get_my_contracts()