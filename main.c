#include <stdio.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <string.h>
#include <unistd.h>

#define MAX_NICKNAME_LEN 25
#define BUFFER_LEN 1024

int UploadUsername(int sock, char *nickname_buf) {
  while (1) {
    char buf[BUFFER_LEN];
    printf("Input nickname: ");
    if (scanf("%1024s", nickname_buf) == 1 &&
        send(sock, nickname_buf, strlen(nickname_buf), 0) >= 0 &&
        memset(buf, 0, BUFFER_LEN) != 0 &&
        recv(sock, buf, BUFFER_LEN, 0) >= 0) {
      if (buf[0] == '+') {
        printf("Connected users: %s\n", buf + 1);
        return 0;
      } else {
        printf("%s\n", buf);
      }
    } else {
      return 1;
    }
  }
}

int IsMyMsg(char *message, char *nickname, size_t nickname_len) {
  return strchr(message, ':') - message == nickname_len && strncmp(message, nickname, nickname_len) == 0;
}

int ClientReader() {
  int sock = 0;
  if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
    printf("Error while getting socket: %d", sock);
    return 1;
  }
  printf("socket: %d\n", sock);
  struct sockaddr_in sock_addr;
  sock_addr.sin_port = htons(48666);
  sock_addr.sin_family = AF_INET;
  sock_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
  int con_code = connect(sock, (struct sockaddr *) &sock_addr, sizeof(sock_addr));
  if (con_code < 0) {
    printf("Error while connecting");
    return 2;
  }
  printf("connected\n");

  char nickname[MAX_NICKNAME_LEN];
  if (UploadUsername(sock, nickname) != 0) {
    printf("Error while uploading nickname");
    return 3;
  }
  size_t nickname_len = strlen(nickname);

  printf("joined\n");

  fd_set fd_all_collection, fd_ready_to_read_collection;
  int maxfd = sock + 1;
  FD_ZERO(&fd_all_collection);
  FD_SET(STDIN_FILENO, &fd_all_collection);
  FD_SET(sock, &fd_all_collection);
  struct timeval tv;
  tv.tv_sec = 2;
  tv.tv_usec = 0;

  char message[BUFFER_LEN];
  memset(message, 0, 1024);
  for (;;) {

    fd_ready_to_read_collection = fd_all_collection;

    select(maxfd, &fd_ready_to_read_collection, NULL, NULL, &tv);

    if (FD_ISSET(STDIN_FILENO, &fd_ready_to_read_collection)) {

      if (scanf("%1024s", message) == 1) {
        if (send(sock, message, strlen(message), 0) < 0) {
          puts("Send failed");
          return 1;
        }
      }
      memset(message, 0, BUFFER_LEN);
    }

    if (FD_ISSET(sock, &fd_ready_to_read_collection)) {
      if (recv(sock, message, BUFFER_LEN, 0) < 0) {
        puts("Error: recv failed");
        break;
      }
      if (!IsMyMsg(message, nickname, nickname_len)) {
        printf("%s\n", message);
      }
      memset(message, 0, BUFFER_LEN);
    }
  }
}

int main() {
  return ClientReader();
}
