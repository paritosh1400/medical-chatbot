let currentChatId = null;

let chatIdToDelete = null;

function loadChats() {
  $.get("/chats", function(chats) {
    $("#chatList").empty();
    chats.forEach(chat => {
      let preview = chat.last_message
        ? chat.last_message.substring(0, 40) + "..."
        : "No messages yet";
      $("#chatList").append(
        `<li class="list-group-item chat-item d-flex justify-content-between align-items-center" data-id="${chat._id}">
           <div>
             <strong>${chat.title}</strong>
             <div class="text-muted small">${preview}</div>
           </div>
           <i class="fas fa-trash delete-chat" data-id="${chat._id}" style="cursor:pointer;"></i>
         </li>`
      );
    });
  });
}

function loadMessages(chatId) {
  $.get(`/chats/${chatId}/messages`, function(messages) {
    $("#messageFormeight").empty();
    messages.forEach(msg => {
      let time = "";
      if (msg.time) {
        const dateObj = new Date(msg.time);
        const hours = dateObj.getHours().toString().padStart(2, '0');
        const minutes = dateObj.getMinutes().toString().padStart(2, '0');
        time = `${hours}:${minutes}`;
      }

      if (msg.role === "user") {
        $("#messageFormeight").append(
          `<div class="d-flex justify-content-end mb-4">
             <div class="msg_cotainer_send">${msg.content}
               <span class="msg_time_send">${time}</span>
             </div>
           </div>`
        );
      } else {
        $("#messageFormeight").append(
          `<div class="d-flex justify-content-start mb-4">
             <div class="msg_cotainer">${msg.content}
               <span class="msg_time">${time}</span>
             </div>
           </div>`
        );
      }
    });
    $("#messageFormeight").scrollTop($("#messageFormeight")[0].scrollHeight);
  });
}

$(document).on("click", ".chat-item", function() {
  currentChatId = $(this).data("id");
  $("#chat_id").val(currentChatId);
  loadMessages(currentChatId);
});

$("#newChatBtn").click(function() {
  $.post("/new_chat", {}, function(data) {
    currentChatId = data.chat_id;
    $("#chat_id").val(currentChatId);
    loadChats();
    $("#messageFormeight").empty();
  });
});

function sendMessage(rawText) {
  const date = new Date();
  const str_time = date.getHours() + ":" + String(date.getMinutes()).padStart(2, "0");

  var userHtml = `<div class="d-flex justify-content-end mb-4">
                    <div class="msg_cotainer_send">${rawText}
                      <span class="msg_time_send">${str_time}</span>
                    </div>
                  </div>`;
  $("#text").val("");
  $("#messageFormeight").append(userHtml);

  $.ajax({
    data: { msg: rawText, chat_id: currentChatId },
    type: "POST",
    url: "/get",
  }).done(function(data) {
    var botHtml = `<div class="d-flex justify-content-start mb-4">
                     <div class="msg_cotainer">${data}
                       <span class="msg_time">${str_time}</span>
                     </div>
                   </div>`;
    $("#messageFormeight").append($.parseHTML(botHtml));
    $("#messageFormeight").scrollTop($("#messageFormeight")[0].scrollHeight);
    loadChats();
  });
}

$("#messageArea").on("submit", function(event) {
  event.preventDefault();
  const rawText = $("#text").val().trim();
  if (!rawText) return;

  if (!currentChatId) {
    $.post("/new_chat", {}, function(data) {
      currentChatId = data.chat_id;
      $("#chat_id").val(currentChatId);
      loadChats();
      sendMessage(rawText);
    });
  } else {
    sendMessage(rawText);
  }
});

$(document).on("click", ".delete-chat", function(event) {
  event.stopPropagation();
  chatIdToDelete = $(this).data("id");
  $("#deleteChatModal").modal("show");
});

$("#confirmDeleteBtn").click(function() {
  if (!chatIdToDelete) return;

  $.ajax({
    url: `/chats/${chatIdToDelete}`,
    type: "DELETE",
    success: function() {
      if (currentChatId === chatIdToDelete) {
        currentChatId = null;
        $("#messageFormeight").empty();
      }
      loadChats();
    },
    error: function() {
      alert("Failed to delete chat.");
    }
  });

  $("#deleteChatModal").modal("hide");
});

$(document).ready(function() {
  loadChats();
});