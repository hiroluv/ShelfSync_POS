import bcrypt


class UserModel:

    @staticmethod
    def hash_password(plain_password):
        # bcrypt requires bytes so encode the string
        password_bytes = plain_password.encode('utf-8')
        # Generate hash
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        # Return as string for dataB
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password, hashed_password):
        #checks plain password input against the hash thingy
        if not hashed_password:
            return False

        try:
            plain_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(plain_bytes, hashed_bytes)
        except ValueError:
            #handle stuff when hash is invalid
            return False