# functions to get data from database 
# path: database/db.py
# if you want to run sqlite3 in terminal, run sqlite3 path/to/database/discord_bot.db
#DISCORD_BOT_DB_PATH is stored in .env file, with Discord bot token

import sqlite3
import os 

class BotDatabase:
    def __init__(self):
        db_file = os.getenv('DISCORD_BOT_DB_PATH', 'discord_bot.db')
        print(f"Using database file: {db_file}")
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row

    
    def get_codeforces_handle(self, discord_server_id, discord_user_id):
        try:
            cursor = self.conn.cursor()
            query = '''
                SELECT codeforces_handle FROM verified_users
                WHERE discord_server_id = ? AND discord_user_id = ?
            '''
            print(f"Executing query: {query} with discord_server_id={discord_server_id}, discord_user_id={discord_user_id}")
            cursor.execute(query, (discord_server_id, discord_user_id))
            row = cursor.fetchone()
            return row['codeforces_handle'] if row else None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    
    #start verification 
    def initiate_verification(self, discord_server_id, discord_user_id, codeforces_handle, problem_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO verification_process (discord_user_id, discord_server_id, codeforces_handle, problem_id)
                VALUES (?, ?, ?, ?)
            ''', (discord_user_id, discord_server_id, codeforces_handle, problem_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error during verification initiation: {e}")

    
    def is_verification_initiated(self, discord_server_id, discord_user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM verification_process WHERE discord_server_id = ? AND discord_user_id = ?
            ''', (discord_server_id, discord_user_id))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"Database error during verification check: {e}")
            return False


    def get_verification_details(self, discord_server_id, discord_user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT codeforces_handle, problem_id FROM verification_process WHERE discord_server_id = ? AND discord_user_id = ?
            ''', (discord_server_id, discord_user_id))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Database error during fetching verification details: {e}")
            return None, None

    

    def complete_verification(self, discord_user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT discord_server_id, codeforces_handle, problem_id FROM verification_process WHERE discord_user_id = ?
            ''', (discord_user_id,))
            row = cursor.fetchone()
            if row:
                self.register_user(row[0], discord_user_id, row[1], row[2])
                cursor.execute('''
                    DELETE FROM verification_process WHERE discord_user_id = ?
                ''', (discord_user_id,))
                self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error during completion of verification: {e}")


    def is_user_verified(self, discord_server_id, discord_user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM verified_users WHERE discord_server_id = ? AND discord_user_id = ?
            ''', (discord_server_id, discord_user_id))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"Database error during verification status check: {e}")
            return False

            
    def reset_registration(self, discord_server_id, discord_user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                DELETE FROM verification_process WHERE discord_server_id = ? AND discord_user_id = ?
            ''', (discord_server_id, discord_user_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error during registration reset: {e}")


    
    def register_user(self, discord_server_id, discord_user_id, codeforces_handle, problem_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO verified_users (discord_server_id, discord_user_id, codeforces_handle, problem_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(discord_server_id, discord_user_id) DO UPDATE SET 
                codeforces_handle = excluded.codeforces_handle,
                problem_id = excluded.problem_id
            ''', (discord_server_id, discord_user_id, codeforces_handle, problem_id))

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")



    def delete_user_registration(self, discord_server_id, discord_user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                DELETE FROM verified_users WHERE discord_server_id = ? AND discord_user_id = ?
            ''', (discord_server_id, discord_user_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error during deleting user registration: {e}")



    def is_user_registered(self, discord_server_id, discord_user_id):  
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM verified_users WHERE discord_server_id = ? AND discord_user_id = ?', (discord_server_id, discord_user_id))
        return cursor.fetchone() is not None
    

    def create_duel_challenge(self, discord_server_id, challenger_id, challengee_id, level, problem_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO duel_challenges (discord_server_id, challenger_id, challengee_id, problem_level, status, problem_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (discord_server_id, challenger_id, challengee_id, level, 'pending', problem_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error during create_duel_challenge: {e}")


    def get_ongoing_duel(self, discord_server_id, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM duel_challenges
                WHERE discord_server_id = ? AND (challenger_id = ? OR challengee_id = ?) AND (status = 'accepted' OR status = 'ongoing' OR status = 'complete')
                ORDER BY duel_id DESC
                LIMIT 1
            ''', (discord_server_id, user_id, user_id))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        

    def get_duel_challenge(self, discord_server_id, challengee_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT duel_id, discord_server_id, challenger_id, challengee_id, problem_level, status, problem_id
            FROM duel_challenges 
            WHERE discord_server_id = ? AND challengee_id = ? AND status = 'pending'
        ''', (discord_server_id, challengee_id))
        return cursor.fetchone()


    def get_specific_duel_challenge(self, discord_server_id, challenger_id, challengee_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT duel_id, discord_server_id, challenger_id, challengee_id, problem_level, status, problem_id
            FROM duel_challenges
            WHERE discord_server_id = ? AND challenger_id = ? AND challengee_id = ? AND status = 'pending'
            ORDER BY duel_id DESC
        ''', (discord_server_id, challenger_id, challengee_id))
        return cursor.fetchone()


    def get_latest_duel_challenge(self, discord_server_id, challengee_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT duel_id, discord_server_id, challenger_id, challengee_id, problem_level, status, problem_id
            FROM duel_challenges
            WHERE discord_server_id = ? AND challengee_id = ? AND status = 'pending'
            ORDER BY duel_id DESC
            LIMIT 1
        ''', (discord_server_id, challengee_id))
        return cursor.fetchone()


    def update_duel_status(self, duel_id, new_status, winner_id=None):
        try:
            cursor = self.conn.cursor()
            if winner_id:
                cursor.execute('''
                    UPDATE duel_challenges SET status = ?, winner_id = ? WHERE duel_id = ?
                ''', (new_status, winner_id, duel_id))
            else:
                cursor.execute('''
                    UPDATE duel_challenges SET status = ? WHERE duel_id = ?
                ''', (new_status, duel_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error during update_duel_status: {e}")


    def get_user_stats(self, discord_server_id, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT duel_wins, duel_losses FROM verified_users
                WHERE discord_user_id = ? AND discord_server_id = ?
            ''', (user_id, discord_server_id))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Database error during get_user_stats: {e}")
            return None
        

    def update_user_stats(self, winner_id, loser_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE verified_users SET duel_wins = duel_wins + 1 WHERE discord_user_id = ?
            ''', (winner_id,))

            cursor.execute('''
                UPDATE verified_users SET duel_losses = duel_losses + 1 WHERE discord_user_id = ?
            ''', (loser_id,))

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error during update_user_stats: {e}")

    def set_current_duel_party_problem(self, discord_server_id, problem_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO current_duel_party (discord_server_id, problem_id)
                VALUES (?, ?)
                ON CONFLICT(discord_server_id) DO UPDATE SET
                problem_id = excluded.problem_id;
            ''', (discord_server_id, problem_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error during setting current duel party problem: {e}")

    def get_current_duel_party_problem(self, discord_server_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT problem_id FROM current_duel_party
                WHERE discord_server_id = ?
            ''', (discord_server_id,))
            row = cursor.fetchone()
            return row['problem_id'] if row else None
        except sqlite3.Error as e:
            print(f"Database error during getting current duel party problem: {e}")
            return None
        

    def set_duel_party_participants(self, discord_server_id, participant_handles):
        try:
            handles_str = ','.join(participant_handles)
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO duel_party_participants (discord_server_id, participant_handles)
                VALUES (?, ?)
                ON CONFLICT(discord_server_id) DO UPDATE SET
                participant_handles = excluded.participant_handles;
            ''', (discord_server_id, handles_str))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error during setting duel party participants: {e}")

    def get_duel_party_participants(self, discord_server_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT participant_handles FROM duel_party_participants
                WHERE discord_server_id = ?
            ''', (discord_server_id,))
            row = cursor.fetchone()
            return row['participant_handles'].split(',') if row else []
        except sqlite3.Error as e:
            print(f"Database error during getting duel party participants: {e}")
            return []
    def close(self):
        self.conn.close()
