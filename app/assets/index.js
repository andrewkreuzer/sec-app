async function processLogin(event) {
  if (event.preventDefault) event.preventDefault();
  else console.log("Cannot cancle reload");
  var username = document.getElementById("username").value;
  var password = document.getElementById("password").value;
  if (username === "" || password === "") {
    console.log("Empty inputs");
    return
  }
  const url = "http://localhost:3000/login";
  const data = { "name": username, "password": password };
  const response = await fetch(url, {
    method: 'POST',
    mode: 'cors',
    cache: 'no-cache',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json'
    },
    redirect: 'follow',
    referrerPolicy: 'no-referrer',
    body: JSON.stringify(data)
  });
  json = await response.json();
  if (json.result === "failed") {
    console.log("Failed to login");
    return
  }

  console.log(username, json);
  window.location.href = '/home';
};

var form = document.getElementById('form');
if (form.attachEvent) {
    form.attachEvent("submit", processLogin);
} else {
    form.addEventListener("submit", processLogin);
}
