      // This is a public sample test API key.
      // Don’t submit any personally identifiable information in requests made with this key.
      // Sign in to see your own test API key embedded in code samples.
const stripe = Stripe("pk_test_51KXlHdKTHHGmVV8P96jo1dkRuadfATW7qZ95wiQnidpbpqNzhcshDDeeqN69cduN1oerEfT8b0rxenb6PCqUD6Lg00j4jrFoR4");

// The items the customer wants to buy
const items = document.getElementById("items").innerHTML
console.log(items)
let elements;
var paymentIntentInfo;

initialize();

document
  .querySelector("#payment-form")
  .addEventListener("submit", handleSubmit);

// Fetches a payment intent and captures the client secret
async function initialize() {
  const response = await fetch("/create-payment-intent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: items,
  });
   paymentIntentInfo = await response.json();
    console.log(paymentIntentInfo)
  const appearance = {
    theme: 'stripe',
  };
  elements = stripe.elements({ appearance, clientSecret:paymentIntentInfo['clientSecret'] });

  const paymentElement = elements.create("payment");
  paymentElement.mount("#payment-element");
}

async function handleSubmit(e) {
  e.preventDefault();
  setLoading(true);
  let customer = {}
  let shipping = {}
  shipping['address'] = {}
  shipping['name'] = document.getElementsByName("name")[0].value
  customer['email'] = document.getElementsByName("email")[0].value
  shipping['address']['line1'] = document.getElementsByName("address")[0].value
  shipping['address']['city'] = document.getElementsByName("city")[0].value
  shipping['address']['state'] = document.getElementsByName("state")[0].value
  shipping['address']['postal_code'] = document.getElementsByName("postal_code")[0].value
  shipping['address']['country'] = document.getElementsByName("country")[0].value
  console.log(JSON.parse(items))

  // Update PaymentIntent with receiver's email, Shipping address, item purchased
  const response = await fetch("/update_payment_intent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({customer,shipping,paymentIntentInfo})
  });
    console.log(response)

   // Confirm payment with Stripe JS
    if(response.status==200) {
      const { error } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          // Make sure to change this to your payment completion page
          return_url: "https://book.zoehu.cf/confirmation",
        }
      });
        console.log(error)
      // This point will only be reached if there is an immediate error when
      // confirming the payment. Otherwise, your customer will be redirected to
      // your `return_url`. For some payment methods like iDEAL, your customer will
      // be redirected to an intermediate site first to authorize the payment, then
      // redirected to the `return_url`.
      if (error.type === "card_error" || error.type === "validation_error") {
        showMessage(error.message);
      } else {
        showMessage("An unexpected error occured.");
      }
      setLoading(false);
    }
    else
    {
        showMessage("Shipping information can't be updated");
    }
}

// ------- UI helpers -------
function showMessage(messageText) {
  const messageContainer = document.querySelector("#payment-message");

  messageContainer.classList.remove("hidden");
  messageContainer.textContent = messageText;

  setTimeout(function () {
    messageContainer.classList.add("hidden");
    messageText.textContent = "";
  }, 4000);
}

// Show a spinner on payment submission
function setLoading(isLoading) {
  if (isLoading) {
    // Disable the button and show a spinner
    document.querySelector("#submit").disabled = true;
    document.querySelector("#spinner").classList.remove("hidden");
    document.querySelector("#button-text").classList.add("hidden");
  } else {
    document.querySelector("#submit").disabled = false;
    document.querySelector("#spinner").classList.add("hidden");
    document.querySelector("#button-text").classList.remove("hidden");
  }
}