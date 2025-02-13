async function api_call_inner(location, data) {
    const response = await fetch(location, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        alert("Request failed");
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const responseData = await response.json();
    if(!responseData["ok"]) {
        alert(responseData["status"]);
    }
    return responseData;
}

async function api_call_data(location, data) {
    try {
        return await api_call_inner(location, data);
    } catch (error) {
        console.error('Error sending POST request:', error);
    }
}

async function api_call_form(location, args, root, button) {
    try {
        const new_data = Object.fromEntries(
            Object.entries(args).map(([k, v]) => [k, document.getElementById(v).value])
        );

        const res = await api_call_inner(location, new_data);
        if(res["ok"]) {
            document.getElementById(root).innerHTML = res["elem"];
            res["code"].forEach((x) => eval(x));
            //document.getElementById(button).disabled = true;
        }
    } catch (error) {
        console.error('Error sending POST request:', error);
    }
}

async function api_call_create(location, type, prefix, button_elem) {
    try {
        let name = prompt("New " + type + " ID: " + prefix);
        if(name == null) {
            return;
        }
        const res = await api_call_inner(location + "/" + type + "/" + prefix + name, {});
        if(res["ok"]) {
            button_elem.insertAdjacentHTML("beforebegin", res["elem"]);
        }
    } catch (error) {
        console.error('Error sending POST request:', error);
    }
}

function create_api_form(location, args, root, button) {
    document.getElementById(button).disabled = true;
    document.getElementById(button).onclick = () => {
        api_call_form(location, args, root, button);
    };
    Object.entries(args).forEach(([k, v]) => {
        document.getElementById(v).oninput = () => {
            document.getElementById(button).disabled = false;
        }
    })
}