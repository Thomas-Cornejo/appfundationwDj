document.addEventListener("DOMContentLoaded", () => {
  const currentPath = window.location.pathname;
  const links = document.querySelectorAll("nav ul li a");

  links.forEach(link => {
    const href = link.getAttribute("href");
    if (currentPath === href || currentPath.startsWith(href + "/")) {
      link.classList.add("border-b-4", "border-indigo-600", "text-indigo-600", "pb-2");
    } else {
      link.classList.add("border-transparent", "text-gray-800", "hover:text-indigo-600", "pb-2");
    }
  });
});
