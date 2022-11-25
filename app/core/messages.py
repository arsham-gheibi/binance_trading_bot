# Emojis
blue_circle = '&#128309;'
green_circle = '&#128994;'
red_circle = '&#128308;'
money_bag = '&#128176;'
money_with_wings = '&#128184;'
woman_shrugging = '&#129335;&#127997;&#8205;&#9792;&#65039;'
check_mark_button = '&#9989;'
no_entry = '&#9940;'
joystick = '&#128377;&#65039;'

# Logger Messages
signal_detail_message = '#{symbol} {entry} {stop_loss} {targets}'
order_created_message = '#{symbol} Order Created for {user}'
order_creation_failed_message = '#{symbol} Order Creation Failed for {user}'
order_cancelled_message = '#{symbol} has been Cancelled for {user}'
order_closed_message = '#{symbol} has been Closed for {user}'
target_created_message = '#{symbol} Target Created for {user}'
stoploss_set_message = '#{symbol} StopLoss Set for {user}'
cant_open_position_due_qty =\
    "#{symbol} Can't Place this Order due Low Quantity {user}"
cant_open_position_due_black_list =\
    "#{symbol} Can't Place this Order, This Symbol is in Black List {user}"

# Notifier Messages

# Percent Messages
percent_reduce_only_target_message = """{emoji}
User: {user_name}
#{symbol} {side} Target {target_number} Achieved &#128640;
Price: ${price}
Quantity: {qty}
Profit/Loss: {profit}%{second_emoji}"""

percent_reduce_only_message = """{emoji}
User: {user_name}
Closed #{symbol} {side}
Price: ${price}
Quantity: {qty}
Profit/Loss: {profit}%{second_emoji}
{closed_due}"""


# Dollar Messages
dollar_reduce_only_target_message = """{emoji}
User: {user_name}
#{symbol} {side} Target {target_number} Achieved &#128640;
Price: ${price}
Quantity: {qty}
Profit/Loss: ${profit}{second_emoji}"""

dollar_reduce_only_message = """{emoji}
User: {user_name}
Closed #{symbol} {side}
Price: ${price}
Quantity: {qty}
Profit/Loss: ${profit}{second_emoji}
{closed_due}"""

not_reduce_only_message = """User: {user_name}
{side} {qty} #{symbol}
Entry: ${price}"""


closed_due_tp = f'All Targets Achived {check_mark_button}'
closed_due_manually = f'Manually Closed {joystick}'
