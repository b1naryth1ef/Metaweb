from flask import Blueprint, render_template, flash, redirect, request, g, session
from util import reqLogin, reqLevel, flashy
from datetime import datetime
from database import *
import stripe

donate = Blueprint('donate', __name__)

@donate.route('/donate/api', methods=['POST'])
def routeDonateAPI(): #@TODO guard against repeat attacks
    if request.json:
        eve = stripe.Event.retrieve(request.json['id'])
        if eve:
            q = Donation.select().where(Donation.stripeid == eve.data.object.id)
            if not q.count():
                print request.json
                return "D:"
            q = q[0]
            #@TODO modify user accounts accordingly
            if eve.type == "charge.succeeded":
                q.active = True
                q.save()
                Notification(user=q.user, title="Donation Recieved!", content="We have recieved your donation of %s$! Thanks for your contribution!" % q.amount).save()
            elif eve.type == "charge.failed":
                q.active = False
                q.save()
                Notification(user=q.user, title="Donation Failed!", content="Your donation of %s$ has failed! Please email support if this is an error!" % q.amount, ntype="error").save()
            elif eve.type == "charge.refunded":
                q.active = False
                q.save()
                Notification(user=q.user, title="Donation Refunded!", content="Your donation of %s$ has been refunded!" % q.amount).save()
            elif eve.type == "charge.dispute.created":
                q.active = False
                q.save()
                Notification(user=q.user, title="Donation Chargeback!", content="A chargeback for your donation of %s$ has been initaited!" % q.amount, ntype="error").save()
    return "Success"

@donate.route("/donate/")
@reqLogin
def routeDonate():
    q = Donation.select().where(Donation.user == g.user)
    return render_template("donate.html", donations=q, pub_key=g.config['STRIPE_PUB_KEY'])

@donate.route("/donate/faq")
@reqLogin
def routeDonateFaq():
    return render_template("donatefaq.html")

@donate.route("/donate/charge", methods=['POST'])
@reqLogin
def routeDonateDo():
    if not 'stripeToken' in request.form.keys() or not 'amount' in request.form.keys():
        flash("Invalid Request!", "error")
        return ":3"
    if not (request.form['amount']+'00').isdigit():
        flash("Invalid Amountt!", "error")
        return ":3"
    if int(request.form['amount']+'00') < 1000:
        flash("You must donate at least 10$!", "error")
        return ":3"
    if int(request.form['amount']+'00') > 10000: #@TODO Fraud warning
        pass

    cus = stripe.Customer.create(email=g.user.email, card=request.form['stripeToken'])

    if cus.delinquent:
        flash("Their is a problem with your account. Please contact support.", "error")
        return ":3"

    charge = stripe.Charge.create(
        customer=cus.id,
        amount=request.form['amount']+"00",
        currency="usd",
        description="Donation to MetaCraft")

    Donation(
        user=g.user,
        stripeid=charge.id,
        customerid=cus.id,
        amount=int(request.form['amount']),
        active=False,
        created=datetime.now()).save()

    flash("You've donated %s dollars! Thank you so much for your contribution to MetaCraft!" % request.form['amount'], "success")
    return ":3"
