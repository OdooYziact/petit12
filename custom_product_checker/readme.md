#Item Master Data Validator

##User interface

This module is adding :
1. A computed field `is_validated` on item master data which is shown when `True` in :
- Item list view as a warning icon on left of the lines
- Quotation lines as a warning icon on left of the line
- Item details view as label on header

2. A flag box `validation forced` in item detail view :
By flagging it (`= True`) the system will by-pass the checked and consider the item as valid.

3. Visual information Which is present as :
- A button "Check Item data"in item detail view. by clicking it, the user receive a popup listing the criteria not respected for the information that the item is valid.
- A warning icon icon on sales lines. The user can also click the icon to see this the popup.
- A warning icon icon on item list view. Here again, the user can also click the icon to see the popup.

##Technical description
This module is fully independent.
So far, due to time constrain, the solution has not been optimized.
By consequences the code is repeated in class product.product and product.template, both being set in model/product.py

The CSS is stored in `static/src/css/style.css` and linked to the views with file views/assets.xml

##Future Optimisation
Goal is that in the future :
- Code no more repeated in product.product and product.template
- Usage of translation instead of French hardcoded
- Create a user interface to set his own validation criteria
