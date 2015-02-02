import os
import requests
import collections

from flask import Flask, render_template, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]

@app.route('/')
def index():	
	# mapping of amounts to types of membership
	amount_product_mapping = {
		1620: "Corporate Members - Yearly", 
		2700: "Members - Lifetime", 
		120: "Family Members - Yearly", 
		30: "Members - Monthly", # old starving hacker rate
		35: "Members - Monthly", # starving hacker
		40: "Members - Monthly", # old regular rate
		50: "Members - Monthly", 
		150: "Corporate - Monthly", # monthly corporate
		200: "Corporate - Monthly", # monthly corporate w/ extra card
		540: "Members - Yearly", 
		10: "Family Members - Monthly", 
		20: "Family Members - Monthly", # an invoice with two family memberships
		60: "monthly + family" #
	}
	# only count last 12 months for these memberships
	yearly_memberships = ["Corporate Members - Yearly", "Family Members - Yearly", "Members - Yearly"]
	# always count these memberships
	lifetime_memberships = ["Members - Lifetime"]
	monthly_memberships = ["Members - Monthly", "Family Members - Monthly"]
	# only products below are shown in output
	headers = yearly_memberships + monthly_memberships + lifetime_memberships + ['Total $']
	
	r = requests.get('https://accounts.dallasmakerspace.org/membership_table.php')
	# sort response by date
	json_response = sorted(r.json(), key=lambda x:x['product_date'])
	
	products_by_month = collections.OrderedDict()
	for row in json_response:
		invoice_amount = int(float(row['invoice_amount']))
		product_count = int(row['product_count'])
		product_date = row['product_date']
		
		if product_date not in products_by_month:
			# create a dict from headers with 0 values, maintain same order as headers using OrderedDict
			products_by_month[product_date] = collections.OrderedDict(zip(headers, [0 for x in headers]))
		
		# split out the monthly + family invoices
		if invoice_amount == 60:
			products_by_month[product_date]["Family Members - Monthly"] += product_count
			products_by_month[product_date]["Members - Monthly"] += product_count
		# split out invoices with 2 family memberships
		elif invoice_amount == 20:
			products_by_month[product_date]["Family Members - Monthly"] += product_count*2
		# -50 = redeemed gift, ignore
		elif invoice_amount == -50:
			pass
		elif invoice_amount in amount_product_mapping:
			products_by_month[product_date][amount_product_mapping.get(invoice_amount)] += product_count
		else:
			flash('Unexpected Invoice Amount Of ' + str(invoice_amount) + ' On ' + product_date) 
		products_by_month[product_date]['Total $'] += invoice_amount*product_count
		
	current_membership = {'Members': 0, 'Family Members': 0, 'Total': 0}
	for count, date in enumerate(reversed(products_by_month)):
		if (count == 0):
			current_month = date
		for p_name, p_count in products_by_month[date].iteritems():
			# add yearly members within the last 12 months to current_membership
			# add lifetime members to current membership
			# add all members from current month
			if ((count == 0) or ((count < 12) and (p_name in yearly_memberships)) or (p_name in lifetime_memberships)) and (p_name != "Total $"):
				if 'Family' in p_name:
					current_membership['Family Members'] += p_count
				else:
					current_membership['Members'] += p_count
				current_membership['Total'] += p_count
						
	return render_template("analysis.html", data=products_by_month, headers=headers, current_membership=current_membership, current_month=current_month)

if __name__ == '__main__':
	port = int(os.environ.get("PORT", 5000))
	app.run(host="0.0.0.0", port=port, debug=True)