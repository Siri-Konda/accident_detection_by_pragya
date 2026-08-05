
function grid_creation(video,location,C_id,n)
{
let i;
for(i=0;i<n;i++)
{
    let container=document.querySelector(".container");

    let grid_element=document.createElement("div");
    grid_element.className="grid-element";
    const video=
    document.createElement("video");

    video.src="video.mp4";
    video.controls=true;
    video.width=640;

    let location=document.createElement("p");
    location.textContent="";

    let C_id=document.createElement("p");
    C_id.textContent="";

    grid_element.append(video);
    grid_element.append(location);
    grid_element.append(C_id);

    container.append(grid_element)
}
}

//ENDPOINT TO ADD TO BACKEND
// @app.get("/camera-id/{filename}")
// async def camera_id(filename:str):
//     return {"camera_id": "CAM-001"}
let array=[];
async function getCameraId(filename)
{
    const resp=await fetch( `http://localhost:8000/camera_id/${filename}`);
    const data=await Response.json();
}
