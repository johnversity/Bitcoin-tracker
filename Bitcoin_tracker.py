import requests
import json
from datetime import datetime
import time
import sys

# Bitcoin color definition
BTC = "\033[38;5;208m"
reset = "\033[0m"

class BitcoinConverterBinance:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        self.symbol = "BTCUSDT"  # BTC/USDT pair on Binance
        
    def get_current_price(self):
        """Gets the current Bitcoin price in USD using Binance"""
        try:
            url = f"{self.base_url}/ticker/price"
            params = {'symbol': self.symbol}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'price' in data:
                return float(data['price'])
            return None
        except requests.exceptions.RequestException as e:
            print(f"Connection error to Binance: {e}")
            # Try alternative endpoint
            return self._get_alternative_price()
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            print(f"Error processing data: {e}")
            return None
        except Exception as e:
            print(f"Error getting current price: {e}")
            return None
    
    def _get_alternative_price(self):
        """Alternative method to get price using different endpoint"""
        try:
            url = f"{self.base_url}/ticker/24hr"
            params = {'symbol': self.symbol}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'lastPrice' in data:
                return float(data['lastPrice'])
            elif 'bidPrice' in data and 'askPrice' in data:
                # Average between bid and ask
                return (float(data['bidPrice']) + float(data['askPrice'])) / 2
            return None
        except:
            return None
    
    def get_historical_data(self, days):
        """Gets historical data from Binance"""
        try:
            # Convert days to milliseconds
            end_time = int(time.time() * 1000)
            start_time = end_time - (days * 24 * 60 * 60 * 1000)
            
            # Determine interval based on requested days
            if days <= 1:
                interval = '15m'  # 15 minutes for 24 hours
                limit = 96  # 24h / 0.25h = 96 points
            elif days <= 7:
                interval = '1h'   # 1 hour for 1 week
                limit = 168  # 7d * 24h = 168 points
            elif days <= 30:
                interval = '4h'   # 4 hours for 1 month
                limit = 180  # 30d * 24h / 4h = 180 points
            else:
                interval = '1d'   # 1 day for longer periods
                limit = min(days, 1000)  # Binance has limit of 1000 records
            
            url = f"{self.base_url}/klines"
            params = {
                'symbol': self.symbol,
                'interval': interval,
                'startTime': start_time,
                'endTime': end_time,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Format data for compatibility
            historical = []
            for candle in data:
                if len(candle) >= 6:  # Each candle has [time, open, high, low, close, ...]
                    timestamp = candle[0]  # Opening time
                    # Use closing price (index 4)
                    price = float(candle[4])
                    historical.append([timestamp, price])
            
            return historical if historical else None
        except requests.exceptions.RequestException as e:
            print(f"Historical data connection error to Binance: {e}")
            return None
        except (KeyError, ValueError, IndexError, json.JSONDecodeError) as e:
            print(f"Error processing historical data: {e}")
            return None
        except Exception as e:
            print(f"Error getting historical data: {e}")
            return None
    
    def get_detailed_price_info(self):
        """Gets detailed 24-hour information"""
        try:
            url = f"{self.base_url}/ticker/24hr"
            params = {'symbol': self.symbol}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return data
        except:
            return None
    
    def show_textual_24h_price(self):
        """Shows price and variation in last 24 hours in text mode"""
        print("\n" + "="*60)
        print(f"{BTC} BITCOIN PRICE🪙 - LAST 24 HOURS {reset}")
        print("="*60)
        
        # Get detailed 24-hour data
        detailed_data = self.get_detailed_price_info()
        
        if detailed_data:
            try:
                current_price = float(detailed_data.get('lastPrice', 0))
                open_price = float(detailed_data.get('openPrice', 0))
                high_price = float(detailed_data.get('highPrice', 0))
                low_price = float(detailed_data.get('lowPrice', 0))
                
                variation = current_price - open_price
                variation_percentage = (variation / open_price) * 100 if open_price else 0
                
                print(f"\n💰 Current price: ${current_price:,.2f}")
                print(f"📈 24h High: ${high_price:,.2f}")
                print(f"📉 24h Low: ${low_price:,.2f}")
                print(f"📊 24h Change: ${variation:+,.2f} ({variation_percentage:+.2f}%)")
                print(f"📈 24h Volume: {float(detailed_data.get('volume', 0)):,.2f} BTC")
                
                if variation > 0:
                    print("📈 Trend: ▲ BULLISH")
                elif variation < 0:
                    print("📉 Trend: ▼ BEARISH")
                else:
                    print("➡ Trend: STABLE")
                
                # Get historical data for chart
                data = self.get_historical_data(1)
                if data:
                    prices = [item[1] for item in data]
                    
                    # Show simple ASCII chart
                    print("\n📊 SIMPLE CHART (ASCII):")
                    print("-" * 50)
                    
                    if len(prices) > 1:
                        price_min_chart = min(prices)
                        price_max_chart = max(prices)
                        price_range = price_max_chart - price_min_chart
                        
                        if price_range > 0:
                            # Show only some points for readability
                            step = max(1, len(prices) // 12)
                            for i in range(0, len(prices), step):
                                height = int(((prices[i] - price_min_chart) / price_range) * 20)
                                timestamp = datetime.fromtimestamp(data[i][0]/1000).strftime('%H:%M')
                                bar = "█" * (height + 1)
                                print(f"{BTC} {timestamp}: {bar} ${prices[i]:,.2f} {reset}")
                    else:
                        print("Insufficient data to display chart")
                
            except (KeyError, ValueError) as e:
                print(f"Error processing detailed data: {e}")
                # Fallback to basic method
                self._show_basic_24h_price()
        else:
            print("Could not get detailed data from Binance.")
            self._show_basic_24h_price()
        
        print("="*60)
    
    def _show_basic_24h_price(self):
        """Backup method to show basic 24h data"""
        data = self.get_historical_data(1)
        
        if not data:
            print("Could not get historical data.")
            current_price = self.get_current_price()
            if current_price:
                print(f"\n {BTC} 💰 Current price: ${current_price:,.2f}{reset}")
            return
        
        prices = [item[1] for item in data]
        current_price = prices[-1] if prices else 0
        price_min = min(prices) if prices else 0
        price_max = max(prices) if prices else 0
        initial_price = prices[0] if prices else 0
        
        variation = current_price - initial_price
        variation_percentage = (variation / initial_price) * 100 if initial_price else 0
        
        print(f"\n {BTC}💰 Current price: ${current_price:,.2f} {reset}")
        print(f"📈 24h High: ${price_max:,.2f}")
        print(f"📉 24h Low: ${price_min:,.2f}")
        print(f"📊 24h Change: ${variation:+,.2f} ({variation_percentage:+.2f}%)")
    
    def show_textual_5days_price(self):
        """Shows price and variation in last 5 days in text mode"""
        print("\n" + "="*60)
        print(f"{BTC}🪙BITCOIN PRICE - LAST 5 DAYS🪙{reset}")
        print("="*60)
        
        data = self.get_historical_data(5)
        
        if not data:
            print("Could not get data from Binance.")
            current_price = self.get_current_price()
            if current_price:
                print(f"\n💰 Current price: ${current_price:,.2f}")
            print("="*60)
            return
        
        prices = [item[1] for item in data]
        dates = [datetime.fromtimestamp(item[0]/1000) for item in data]
        
        current_price = prices[-1] if prices else 0
        price_min = min(prices) if prices else 0
        price_max = max(prices) if prices else 0
        initial_price = prices[0] if prices else 0
        
        variation = current_price - initial_price
        variation_percentage = (variation / initial_price) * 100 if initial_price else 0
        
        print(f"\n{BTC}💰 Current price: ${current_price:,.2f} {reset}")
        print(f"📈 5-Day High: ${price_max:,.2f}")
        print(f"📉 5-Day Low: ${price_min:,.2f}")
        print(f"📊 5-Day Change: ${variation:+,.2f} ({variation_percentage:+.2f}%)")
        
        # Show daily summary
        print("\n📅 DAILY SUMMARY:")
        print("-" * 50)
        
        if len(prices) >= 5:
            # Group by approximate day
            prices_by_day = {}
            for i, (date, price) in enumerate(zip(dates, prices)):
                day_key = date.strftime('%d/%m')
                if day_key not in prices_by_day:
                    prices_by_day[day_key] = []
                prices_by_day[day_key].append(price)
            
            for day, day_prices in list(prices_by_day.items())[-5:]:  # Last 5 days
                if day_prices:
                    average_price = sum(day_prices) / len(day_prices)
                    print(f"{day}: ${average_price:,.2f} (average)")
        else:
            # Show available points
            step = max(1, len(prices) // 5)
            for i in range(0, len(prices), step):
                date = dates[i].strftime('%d/%m %H:%M')
                price = prices[i]
                print(f"{date}: ${price:,.2f}")
        
        print("="*60)
    
    def convert_bitcoin_to_usd(self):
        """Converts an amount of Bitcoin🪙 to USD"""
        print("\n" + "="*50)
        print(f"{BTC}🪙BITCOIN TO USD CONVERTER (Binance)🪙 {reset}")
        print("="*50)
        
        price_btc = self.get_current_price()
        
        if not price_btc:
            print("⚠ Could not get current price from Binance.")
            print("   Service may be temporarily unavailable.")
            use_default = input("\nUse reference price of $50,000? (y/n): ").lower()
            if use_default == 'y':
                price_btc = 50000.0
                print(f"\nUsing reference price: ${price_btc:,.2f}")
            else:
                try:
                    price_btc = float(input("\nEnter price manually: $"))
                except ValueError:
                    print("Invalid price. Using $50,000 as default.")
                    price_btc = 50000.0
        else:
            print(f"\n {BTC} ✅ Current price: 1 BTC🪙 = ${price_btc:,.2f} {reset}")
            print("   Source: Binance API")
        
        while True:
            try:
                amount = input(f"\n{BTC} Enter amount of Bitcoin🪙: {reset}")
                amount_btc = float(amount)
                
                if amount_btc <= 0:
                    print("Error: Amount must be greater than 0")
                    continue
                    
                break
            except ValueError:
                print("Error: Enter a valid number")
        
        result = amount_btc * price_btc
        
        print("\n" + "="*50)
        print("RESULT:")
        print("="*50)
        print(f"{BTC}📊 Bitcoin amount: {amount_btc:.8f} BTC {reset}")
        print(f"{BTC}💰 Current price: ${price_btc:,.2f} USD/BTC {reset}")
        print(f"{BTC}💵 Total value: ${result:,.2f} USD {reset}")
        print("="*50)
        
        input("\nPress Enter to continue...")

def show_simple_menu():
    """Simplified main menu"""
    converter = BitcoinConverterBinance()
    
    while True:
        # Clear screen
        print("\033c", end="")
        
        print("="*60)
        print(f" {BTC}     🪙BITCOIN TRACKER & CONVERTER🪙 {reset}")
        print("="*60)
        print("Data source: Binance.com")
        print("Pair: BTC/USDT")
        print("="*60)
        
        price = converter.get_current_price()
        if price:
            print(f"\n {BTC}💰 Current Bitcoin🪙 price: ${price:,.2f} 💸USD{reset}")
            print(f"   📅 Last update: {datetime.now().strftime('%H:%M:%S')}")
        else:
            print("\n⚠ Could not get current price from Binance")
            print("   Check your internet connection or try again later")
        
        print("\nMAIN MENU:")
        print("1. 📊 Price and 24-hour analysis")
        print("2. 📈 5-day analysis")
        print("3. 🪙💱💸 Bitcoin to USD converter")
        print("4. 🔄 Update price")
        print("5. 🚪 Exit")
        print("\n" + "="*60)
        
        option = input("\nSelect an option (1-5): ")
        
        if option == "1":
            converter.show_textual_24h_price()
            input("\nPress Enter to continue...")
            
        elif option == "2":
            converter.show_textual_5days_price()
            input("\nPress Enter to continue...")
            
        elif option == "3":
            converter.convert_bitcoin_to_usd()
            
        elif option == "4":
            print("\nUpdating price from Binance🪙...")
            new_price = converter.get_current_price()
            if new_price:
                print(f"✅ New price: ${new_price:,.2f}")
                print(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
            else:
                print("❌ Could not update price")
            time.sleep(2)
            
        elif option == "5":
            print("\nThank you for using Bitcoin Tracker!")
            print("Powered by Binance API")
            print("See you soon! 👋\n")
            break
            
        else:
            print("\n❌ Invalid option")
            time.sleep(1)

if __name__ == "__main__":
    try:
        import requests
        print("Starting 🪙Bitcoin Tracker with Binance API...")
        print("Connecting to Binance...")
        time.sleep(1)
        show_simple_menu()
    except ImportError:
        print("Error: You need to install requests")
        print("Install with: pip install requests")
        sys.exit(1)