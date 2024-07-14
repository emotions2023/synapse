window.onload = function () {
    const apiResponse = JSON.parse(localStorage.getItem('apiResponse'));
    const messageContent = JSON.parse(apiResponse.choices[0].message.content);
  
    document.getElementById('name').innerText = messageContent.name;
    document.querySelector('.name').textContent = messageContent.name;
    const detailsList = document.querySelector('.details-list');
    detailsList.rows[0].cells[1].textContent = messageContent.birth;
    detailsList.rows[1].cells[1].textContent = messageContent.death;
    detailsList.rows[2].cells[1].textContent = messageContent.cemetery;
    detailsList.rows[3].cells[1].textContent = messageContent.business;
    detailsList.rows[4].cells[1].textContent = messageContent.language;
    detailsList.rows[5].cells[1].textContent = messageContent.nationality;
    detailsList.rows[6].cells[1].textContent = messageContent.education;
    detailsList.rows[7].cells[1].textContent = messageContent.lastEducation;
    detailsList.rows[8].cells[1].textContent = messageContent.periodOfActivity;
    detailsList.rows[9].cells[1].textContent = messageContent.genre;
  
    document.getElementById('upbringing').textContent = messageContent.upbringing;
    document.getElementById('deathDetails').textContent = messageContent.deathDetails;
    document.querySelector('.others').textContent = messageContent.others;
  };
  
  const imageData = localStorage.getItem('userImage');
  if (imageData) {
    const img = document.createElement('img');
    img.src = imageData;
    img.style.width = '100%';
    img.style.height = '100%';
  
    const userPicture = document.querySelector('.user-picture');
    userPicture.textContent = '';
    userPicture.appendChild(img);
  }
  
  document.addEventListener('DOMContentLoaded', (event) => {
    const lastUpdatedParagraph = document.getElementById('last-updated');
    lastUpdatedParagraph.textContent = `最終更新: ${new Date().toISOString().split('T')[0]}`;
  });
  