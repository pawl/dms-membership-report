import pandas as pd
import os

from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def index():
	df = pd.read_json('http://dallasmakerspace.org/misc/membership_table.php')

	# mapping of 
	invoice_amount_dict = {
		150: "monthly", 
		1620: "yearly corporate", 
		2700: "lifetime", 
		10: "family", 
		120: "yearly family", 
		30: "monthly", 
		35: "monthly", 
		40: "monthly", 
		50: "monthly", 
		540: "yearly", 
		60: "monthly + family", 
		20: "family"
	}
	def determine_type(row):
		return invoice_amount_dict[row['invoice_amount']]

	# hack to split out the monthly + family invoices	
	df['membership_type'] = df.apply(determine_type, axis=1)
	temporary_df = df[(df.invoice_amount == 60)]
	temporary_df['invoice_amount'] = 10
	temporary_df['membership_type'] = "family"
	temporary_df2 = df[(df.invoice_amount == 60)]
	temporary_df2['invoice_amount'] = 50
	temporary_df2['membership_type'] = "monthly"
	new_df = df[(df.membership_type != "monthly + family")].append(temporary_df).append(temporary_df2)
	return render_template("analysis.html", name="Membership Data", data=new_df.groupby(["product_date","membership_type"]).sum().unstack(1).fillna(0)["product_count"].to_html(classes="table table-striped"))
	
if __name__ == '__main__':
	port = int(os.environ.get("PORT", 5000))
	app.run(host="0.0.0.0", port=port)