# Set identification from install inputs
if [[ -n ${ARCH_USER_NAME//[[:space:]]/} ]]; then
  git config --global user.name "$ARCH_USER_NAME"
fi

if [[ -n ${ARCH_USER_EMAIL//[[:space:]]/} ]]; then
  git config --global user.email "$ARCH_USER_EMAIL"
fi
