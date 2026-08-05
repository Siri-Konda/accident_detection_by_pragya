
function grid_creation(video,location,C_id,n)
{
let i;
for(i=0;i<n;i++)
{
    let container=document.querySelector(".container");

    let grid_element=document.createElement("div");
    grid_element.className="grid-element";
    let video=;//insert video file;
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