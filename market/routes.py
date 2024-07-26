

from market import app, db
from flask import jsonify, render_template, redirect, url_for, flash, request
from market.forms import AddItemForm, PurchaseItemForm, RegisterForm, LoginForm, SearchForm, SellItemForm
from market.models import Item, User
from flask_login import login_user,logout_user,login_required, current_user

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/market',  methods=['GET', 'POST'])
@login_required
def market_page():
    purchase_form = PurchaseItemForm()
    selling_form = SellItemForm()
    if request.method == 'POST':
        #purchase item logic
        purchased_item = request.form.get('purchased_item')
        p_item_object = Item.query.filter_by(name=purchased_item).first()
        if p_item_object:
            if current_user.can_purchase(p_item_object):
                p_item_object.owner = current_user.id 
                current_user.budget -= p_item_object.price 
                db.session.commit()
                flash(f"Congratulations! You purchased {p_item_object.name} for {p_item_object.price}$", category='success')

            else:
                flash(f'Unfortunately, You do not have enough money to puchase { p_item_object.name}', category='danger')
        #sell item logic
        sold_item = request.form.get('sold_item')
        s_item_object = Item.query.filter_by(name=sold_item).first()
        if s_item_object:
            if current_user.can_sell(s_item_object):
                s_item_object.owner = None
                current_user.budget += s_item_object.price
                db.session.commit()
                flash(f"Congratulations! You sold {s_item_object.name} back to market", category='success')

            else:
                flash(f'unfortunately you do not own item {s_item_object.name}', category='danger')
        return redirect(url_for('market_page'))
    
    if request.method == 'GET':
        items = Item.query.filter_by(owner=None)
        owned_items = Item.query.filter_by(owner=current_user.id )
        return render_template('market.html', items=items, purchase_form=purchase_form, owned_items=owned_items, selling_form=selling_form)

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              email_address=form.email_address.data,
                              password=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f' Account created successfully! You are logged in as : {user_to_create.username}', category='success')

        return redirect(url_for('market_page'))
    
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(f'there was an error while creating a user: {err_msg}', category='danger')


    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(attempted_password=form.password.data):
            login_user(attempted_user)
            flash(f'You are logged in as : {attempted_user.username}', category='success')
            return redirect(url_for('market_page'))
        else:
            flash('incorrect username or password', category='danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout_page():
    logout_user()
    flash('you have been loged out ', category='info')
    return redirect(url_for('home_page'))




#admin user
@app.route('/admin_page')
def admin_page():
    return render_template('admin_page.html')

@app.route('/manage_product')
def manage_product():
    form = AddItemForm()
    purchase_form = PurchaseItemForm()
    items = Item.query.all()
    return render_template('admin_manage_product.html', items=items, form=form, purchase_form=purchase_form)

@app.route('/add_item', methods=['GET','POST'])
@login_required
def add_item():
    form = AddItemForm()
    if form.validate_on_submit():
        item_to_add = Item(name=form.name.data,price=form.price.data, barcode=form.barcode.data, description=form.description.data )
        db.session.add(item_to_add)
        db.session.commit()
        print("databse add")
        flash(f' {item_to_add.name} added to market', category='success')
        return redirect(url_for('manage_product'))
    
    else:
        for err_msg in form.errors.values():
            flash(f'therser: {err_msg}', category='danger')
        #flash('Error in form submission', category='danger')
        # Re-render the template with the form to show validation errors
        return render_template('home.html', form=form)

@app.route('/delete_item/<int:item_id>')
@login_required
def delete_item(item_id):
    item_to_delete = Item.query.get_or_404(item_id)
    try:
        db.session.delete(item_to_delete)
        db.session.commit()
        flash(f'Item {item_to_delete.name} has been deleted', 'success')
        return redirect(url_for('manage_product'))
    except:
        flash(f'whoops some problem for deleting item {item_to_delete.name}', category='danger')
        return redirect(url_for('manage_product'))

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item_to_edit = Item.query.get_or_404(item_id)
    form = AddItemForm()
    if form.validate_on_submit():
        item_to_edit.name = form.name.data
        item_to_edit.barcode = form.barcode.data
        item_to_edit.price = form.price.data
        item_to_edit.description = form.description.data

        db.session.add(item_to_edit)
        db.session.commit()
        flash('Item has been updated', category= 'success')
        return redirect(url_for('manage_product'))


@app.route('/get_item/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    item_data = {
        'id': item.id,
        'name': item.name,
        'barcode': item.barcode,
        'price': item.price,
        'description': item.description
    }

    print(item)
    return jsonify(item_data)

@app.route('/admin_login_page', methods=['GET','POST'])
def admin_login_page():
    form = LoginForm()
    if form.validate_on_submit():
        admin_data = User.query.filter_by(username=form.username.data).first()
        if admin_data.username == "Admin_123" and admin_data.check_password_correction(attempted_password = form.password.data):
            login_user(admin_data)
            flash(f'You are logged in as : {admin_data.username}', category='success')
            return redirect(url_for('admin_page'))
        else:
            flash('incorrect username or password', category='danger')

    return render_template('admin_login.html', form=form)


@app.route('/user_data', methods=['GET', 'POST'])
def get_all_user():
    users = User.query.all()
    

    return render_template('admin_userdata.html', users=users)

@app.route('/user_owned_items/<int:user_id>', methods=['GET', 'POST'])
def user_owned_items(user_id):
    items = Item.query.filter_by(owner=user_id).all()
    item_data = [{'name': item.name} for item in items]
    return jsonify(item_data)


#search
@app.context_processor
def admin_page():
    form = SearchForm()
    return dict(form=form)

@app.route('/search', methods=['POST'])
def search():
    form = SearchForm()
    users = User.query
    if request.method == 'POST' and form.validate_on_submit():
        searched_user = form.searched.data
        users = users.filter(User.username.like('%' + searched_user + '%'))
        users = users.order_by(User.id).all()
        return render_template('search.html', form=form , searched_user=searched_user, users=users)
    