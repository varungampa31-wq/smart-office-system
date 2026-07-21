document.getElementById("loginForm").addEventListener("submit",async function(e){

e.preventDefault();

const username=document.getElementById("username").value;

const password=document.getElementById("password").value;

const response=await fetch(BASE_URL+"/token/",{

method:"POST",

headers:{

"Content-Type":"application/json"

},

body:JSON.stringify({

username,

password

})

});

const data=await response.json();

if(response.ok){

localStorage.setItem("access",data.access);

localStorage.setItem("refresh",data.refresh);

window.location.href="dashboard.html";

}

else{

document.getElementById("message").innerHTML="Invalid Username or Password";

}

});